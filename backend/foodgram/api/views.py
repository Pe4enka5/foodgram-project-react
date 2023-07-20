from api.filters import RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAdminAuthorOrReadOnly
from api.serializers import (FavouriteSerializer, IngredientsSerializer,
                             RecipeAddSerializer, RecipeFullSerializer,
                             ShoppingCartSerializer, SubscribeSerializer,
                             SubscriptionsSerializer, TagsSerializer)
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Subscribe

User = get_user_model()


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Работа с информацией о тэгах"""
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Работа с информацией об ингредиентах"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (AllowAny, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Работа с рецептами. Редактирование рецептов.
    Добавление/удаление в/из избранное, список покупок.
    Скачивание списка покупок"""
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeFullSerializer
        return RecipeAddSerializer

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': pk}
            serializer = FavouriteSerializer(
                data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            user = request.user
            recipe = get_object_or_404(Recipe, id=pk)
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAdminAuthorOrReadOnly, ])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': pk}
            serializer = ShoppingCartSerializer(data=data,
                                                context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            user = request.user
            recipe = get_object_or_404(Recipe, id=pk)
            shopping_cart = get_object_or_404(ShoppingCart,
                                              user=user, recipe=recipe)
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=[permissions.IsAuthenticated, ])
    def download_shopping_cart(self, request):
        ingredients = request.user.shopping_cart.all().values_list(
            'recipe__ingredients__name',
            'recipe__ingredients__recipeingredients__amount',
            'recipe__ingredients__measurement_unit')
        list = {}
        for ingredient in ingredients:
            name = ingredient[0]
            amount = ingredient[1]
            measurement_unit = ingredient[2]
            if name not in list:
                list[name] = {
                    'measurement_unit': measurement_unit,
                    'amount': amount
                }
            else:
                list[name]['amount'] += amount
        shopping_cart = []
        for item in list:
            shopping_cart.append(f'{item} - {list[item]["amount"]} '
                                 f'{list[item]["measurement_unit"]} \n')
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_cart.txt"'
        return response


class SubscribeView(APIView):
    """Добавление/удаление подписок пользователя"""
    def post(self, request, id):
        following = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={'user': request.user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        following = get_object_or_404(User, id=id)
        if not Subscribe.objects.filter(user=request.user,
                                        following=following).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscribe.objects.get(user=request.user.id,
                              following=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    """Работа с информацией о подписках пользователя"""
    serializer_class = SubscriptionsSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
