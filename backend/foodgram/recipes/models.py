from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Tag(models.Model):
    """Модель тэга"""
    name = models.CharField(
        max_length=settings.MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Название тэга'
    )
    color = models.CharField(
        max_length=settings.MAX_LENGTH_TAG_COLOR,
        verbose_name='Цветовой HEX-код'
    )
    slug = models.CharField(
        max_length=settings.MAX_LENGTH_TAG_SLUG,
        unique=True,
        verbose_name='Уникальный Slug'
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(
        max_length=settings.MAX_LENGTH_INGREDIENT_NAME,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=settings.MAX_LENGTH_INGREDIENT_MEASUREMENT_UNUT,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [models.UniqueConstraint(
                       fields=('name', 'measurement_unit'),
                       name='unique_ingredient')]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=settings.MAX_LENGTH_RECIPE_NAME,
        verbose_name='Название рецепта',
        unique=True
    )
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='recipes/'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(settings.MIN_COOKING_TIME_IN_MINUTES,
                              'Время приготовления блюда не может быть меньше'
                              f'{settings.MIN_COOKING_TIME_IN_MINUTES} мин.'),
            MaxValueValidator(settings.MAX_COOKING_TIME_IN_MINUTES,
                              'Время приготовления блюда не может быть больше'
                              f'{settings.MAX_COOKING_TIME_IN_MINUTES} мин.'),
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель ингредиентов в рецепте"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(settings.MIN_NUMBERS_OF_INDIGRIENDS,
                              'Количество ингредиентов не может быть меньше'
                              f'{settings.MIN_NUMBERS_OF_INDIGRIENDS} ед.'),
            MaxValueValidator(settings.MAX_NUMBERS_OF_INDIGRIENDS,
                              'Количество ингредиентов не может быть больше'
                              f'{settings.MAX_NUMBERS_OF_INDIGRIENDS} ед.'),
        ]
    )

    class Meta:
        default_related_name = 'recipeingredients'
        verbose_name = 'Состав рецепта'
        verbose_name_plural = 'Состав рецепта'


class FavoriteAndShoppingCart(models.Model):
    """Общая модель для избранного и списка покупок"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)ss'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(
            fields=('user', 'recipe'),
            name='unique_recipe_in_user_%(class)s')]
        ordering = ('-pud_date', )

    def __str__(self):
        return (f'{self.user.username} - {self.recipe.name}'
                f'({self._meta.verbose_name})')


class Favorite(FavoriteAndShoppingCart):
    """Модель избранного рецепта"""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(FavoriteAndShoppingCart):
    """Модель списка покупок пользователя"""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
