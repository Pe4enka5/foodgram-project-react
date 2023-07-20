from django.contrib.auth import get_user_model
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from users.models import Subscribe

User = get_user_model()


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов"""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""
    class Meta:
        model = Ingredient
        fields = '__all__'


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password', 'id')


class CustomUserSerializer(UserSerializer):
    """Сериализатор для информации о пользователях"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=self.context['request'].user,
            following=obj).exists()


class RecipeinfoSerializer(serializers.ModelSerializer):
    """Сериализатор о краткой информации рецепта"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор об информации ингредиентов в рецепте"""
    ingredient = IngredientsSerializer(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт"""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeFullSerializer(serializers.ModelSerializer):
    """Сериализатор о полной информации рецепта"""
    tags = TagsSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(
            recipe=obj).prefetch_related('ingredient')
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipe=obj,
                                           user=request.user).exists()


class RecipeAddSerializer(serializers.ModelSerializer):
    """Сериализатор редактирования рецепта"""
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    cooking_time = serializers.IntegerField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')

    def validate_ingredients(self, data):
        ingredients = self.get_initial()['ingredients']
        if not ingredients:
            raise ValidationError('Нужно выбрать минимум 1 ингредиент!')
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise ValidationError('Количество должно быть положительным!')
        ingredients_count = len(ingredients)
        ingredients_set = len(set([i['id'] for i in ingredients]))
        if ingredients_count > ingredients_set:
            raise ValidationError('Ингредиенты не должны повторяться')
        return data

    def validate_tags(self, data):
        tags = self.get_initial()['tags']
        if not tags:
            raise serializers.ValidationError('Нужно добавить тэг')
        unique_tags = set()
        for item in tags:
            if item in unique_tags:
                raise serializers.ValidationError('Тэги должны быть разными!')
            unique_tags.add(item)
        return data

    def validate_cooking_time(self, data):
        if data <= 0:
            raise ValidationError('Время готовки должно быть положительным')
        return data

    def add_recipe_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            if (RecipeIngredient.objects.
                    filter(recipe=recipe, ingredient=ingredient_id).exists()):
                amount += F('amount')
            RecipeIngredient.objects.update_or_create(
                recipe=recipe, ingredient=ingredient_id,
                defaults={'amount': amount})

    def create(self, validated_data):
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_recipe_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, recipe, validated_data):
        recipe.name = validated_data.get('name', recipe.name)
        recipe.text = validated_data.get('text', recipe.text)
        recipe.cooking_time = validated_data.get('cooking_time',
                                                 recipe.cooking_time)
        recipe.image = validated_data.get('image', recipe.image)
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self.add_recipe_ingredients(ingredients, recipe)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.set(tags_data)
        recipe.save()
        return recipe

    def to_representation(self, recipe):
        data = RecipeinfoSerializer(
            recipe, context=self.context).data
        return data


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор об избранном рецепте"""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в избранное!')
        return data

    def to_representation(self, instance):
        return RecipeinfoSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок"""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в список покупок')
        return data

    def to_representation(self, instance):
        return RecipeinfoSerializer(instance.recipe).data


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор о подписках пользователя"""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeinfoSerializer(recipes, many=True,
                                    context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.follower.filter(user=obj, following=request.user).exists()


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для редактирования подписок пользователя"""
    class Meta:
        model = Subscribe
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'following'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['following']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionsSerializer(
            instance.following, context={'request': request}
        ).data
