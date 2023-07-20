from api.views import (IngredientViewSet, RecipeViewSet, SubscribeView,
                       SubscriptionsViewSet, TagsViewSet)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users/subscriptions', SubscriptionsViewSet,
                basename='subscriptions')

urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:id>/subscribe/', SubscribeView.as_view(),
         name='subscribe'),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
