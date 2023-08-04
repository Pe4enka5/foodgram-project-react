# Foodgram
Сайт для добавления своих рецептов и промотра других!
## Основные функции:
- Добавление своих рецептов;
- Просмотр чужих рецептов;
- Подписка на авторов рецептов;
- Составленрия списка продуктов из понравившихся рецептов;
- Добавление в избранное лучших рецептов.

## Используемый стек:
Python, Django, DRF, Djoser, Gunicorn, Nginx, Docker

## Для запуска Вам понадобиться:
- Создать папку 'foodgram' и в ней создать файл с переменным .env . Пример шаблона представлен в файле .env.example
- Скопируйте файл 'nginx.conf' в папку 'foodgram'
- Скопируйте файл 'docker-compose.production.yml' в папку 'foodgram' и запустите Docker
```
sudo docker compose -f docker-compose.production.yml up -d
``` 
- Выполните миграции, соберите статические файлы бэкенда и скопируйте их в /static/
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /static/
``` 
- Создать суперюзера
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
Никнейм: ZePe4
Пароль: Gtxthbwf89
```
- Все готово! Сайт доступен по адресу https://foodgrampe4.hopto.org/

### Автор: 
Андрей Pe4enka5 Печерица