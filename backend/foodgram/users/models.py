from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F

from users.validators import validate_username


class User(AbstractUser):
    """Модель кастомного юзера"""
    username = models.CharField(
        max_length=settings.MAX_LENGTH_USERNAME,
        unique=True,
        verbose_name='Никнейм',
        validators=(validate_username, )
    )
    first_name = models.CharField(
        max_length=settings.MAX_LENGTH_FIRST_NAME,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=settings.MAX_LENGTH_LAST_NAME,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        max_length=settings.MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name='Почта'
    )
    password = models.CharField(
        max_length=settings.MAX_LENGTH_PASSWORD,
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
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписки'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following'),
            models.CheckConstraint(
                check=~Q(following=F('user')),
                name='you_cant_subscribe_to_yourself')
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
