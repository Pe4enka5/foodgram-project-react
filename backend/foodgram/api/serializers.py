from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscribe

User = get_user_model()


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей"""
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
        if request.user.is_authenticated:
            return obj.following.filter(
                user=request.user, following=obj
            ).exists()
        return False


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
        ingredients = (obj.recipeingredients.filter(recipe=obj))
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.favorites.filter(recipe=obj, user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.shoppingcarts.filter(recipe=obj,
                                            user=request.user).exists()
        return False


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

    def validate_ingredients(self, ingredients_data):
        ingredients = ingredients_data
        if not ingredients:
            raise ValidationError('Нужно выбрать минимум 1 ингредиент!')
        unique_ingredients = set()
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise ValidationError('Количество должно быть положительным!')
            unique_ingredients.append(ingredient.get('id'))
        if len(ingredients) > len(unique_ingredients):
            raise ValidationError('Ингредиенты не должны повторяться')
        return ingredients

    def validate_tags(self, tags_data):
        tags = tags_data
        if not tags:
            raise serializers.ValidationError('Нужно добавить тэг')
        unique_tags = set()
        for item in tags:
            if item in unique_tags:
                raise serializers.ValidationError('Тэги должны быть разными!')
            unique_tags.add(item)
        return tags

    def add_recipe_ingredients(self, ingredients, recipe):
        recipe_ingredients = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            recipe_ingredients.append(
                RecipeIngredient(recipe=recipe, ingredient_id=ingredient_id,
                                 amount=amount)
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_recipe_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance.ingredients.clear()
        self.add_recipe_ingredients(ingredients, instance)
        if tags is not None:
            instance.tags.set(tags)
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        data = RecipeinfoSerializer(
            recipe, context=self.context).data
        return data


class FavoriteAndShoppingCartSerializer(serializers.ModelSerializer):
    """Общий сериализер для Избранного и Списка покупок"""
    class Meta:
        fields = ('user', 'recipe')
        abstract = True

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в '
                                  f'{self.Meta.model._meta.verbose_name}!')
        return data


class FavouriteSerializer(FavoriteAndShoppingCartSerializer):
    """Сериализатор об избранном рецепте"""
    class Meta(FavoriteAndShoppingCartSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок"""
    class Meta(FavoriteAndShoppingCartSerializer.Meta):
        model = ShoppingCart


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор о подписках пользователя"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = User
        fields = (
            CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
            )
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


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для редактирования подписок пользователя"""
    class Meta:
        model = Subscribe
        fields = ('user', 'following')
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
