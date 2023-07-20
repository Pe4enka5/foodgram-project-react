from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from users.validators import validate_username


class User(AbstractUser):
    """Модель кастомного юзера"""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Никнейм',
        validators=[validate_username, ]
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Почта'
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписки'
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'following'],
            name='unique_following')]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.following.username}'
