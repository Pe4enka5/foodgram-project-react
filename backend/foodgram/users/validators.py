import re

from django.core.exceptions import ValidationError
from django.conf import settings


def validate_username(username):
    if username in settings.BANNED_USERNAME:
        raise ValidationError(f'Использовать имя "{username}" запрещено')

    result = re.sub(r'[\w.@+-]+', '', username)
    if result:
        result_unique = ''.join(set(result))
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы: '
            f'{result_unique}'
        )
    return username
