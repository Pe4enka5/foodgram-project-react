from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.mixins import CreateDeleteModelMixin
from api.pagination import CustomPagination
from api.permissions import IsAdminAuthorOrReadOnly
from api.serializers import (FavouriteSerializer, IngredientsSerializer,
                             RecipeAddSerializer, RecipeFullSerializer,
                             ShoppingCartSerializer, SubscribeSerializer,
                             SubscriptionsSerializer, TagsSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
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
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = IngredientFilter
    search_fields = ('name', )
    pagination_class = None


class RecipeViewSet(CreateDeleteModelMixin, viewsets.ModelViewSet):
    """Работа с рецептами. Редактирование рецептов.
    Добавление/удаление в/из избранное, список покупок.
    Скачивание списка покупок"""
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeFullSerializer
        return RecipeAddSerializer

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        return self.create_obj(data, request, FavouriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        kwargs = {'user': request.user,
                  'recipe': get_object_or_404(Recipe, id=pk)}
        return self.delete_obj(Favorite, **kwargs)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        return self.create_obj(data, request, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        kwargs = {'user': request.user,
                  'recipe': get_object_or_404(Recipe, id=pk)}
        return self.delete_obj(ShoppingCart, **kwargs)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
            amount=Sum('amount'))
        shopping_cart = ['Список покупок:']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient[
                'ingredient__measurement_unit']
            amount = ingredient['amount']
            shopping_cart.append(f'\n{name} - {amount}, {measurement_unit}')
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class SubcsribeView(CreateDeleteModelMixin, UserViewSet):
    """Работа с подписками. Получение всего списка
    Подписка и отписка от других авторов"""
    queryset = User.objects.all()

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        following = get_object_or_404(User, id=id)
        data = {'user': request.user.id, 'following': following.id}
        return self.create_obj(data, request, SubscribeSerializer)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        following = get_object_or_404(User, id=id)
        if not Subscribe.objects.filter(user=request.user,
                                        following=following).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        kwargs = {'user': request.user, 'following': following}
        return self.delete_obj(Subscribe, **kwargs)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page, context={'request': request}, many=True)
        return self.get_paginated_response(serializer.data)
