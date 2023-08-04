from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter


from api.views import (IngredientViewSet, RecipeViewSet, SubcsribeView,
                       TagsViewSet)

router = DefaultRouter()
router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', SubcsribeView, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('docs/', TemplateView.as_view(template_name='redoc.html'),
         name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
