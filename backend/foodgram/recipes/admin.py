from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorited')
    list_filter = ('name', 'author', 'tags')
    inlines = (RecipeIngredientInLine, )

    def in_favorited(self, obj):
        return obj.favorites.all().count()


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
