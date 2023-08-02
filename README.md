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
- Установить на сервер Docker:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
``` 
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
- Настройте Nginx, проверьте, что все - ок и перезапустите программу
```
nano /etc/nginx/sites-enabled/default
sudo nginx -t
sudo service nginx reload 
```
- Создать суперюзера
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
Никнейм: ZePe4
Пароль: Gtxthbwf89
```
- Все готово!

### Автор: 
Андрей Pe4enka5 Печерица