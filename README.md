# market-api-service
Бэкенд веб-сервиса для сравнения цен

## 🛸 Инструменты
Для выполнения задания я пользовался **django**, **django-rest-framework** и **postgreSQL**.

## 🛠 Ставим
0. сначала заполучите [докер](https://www.docker.com/get-started/)
1. стяните репозиторий и перейдите в директорию проекта
```
> git clone https://github.com/fefefefta/market-api-service
> cd market-api-service
```
2. добавьте .env файл в каталог market-api-service/market/market
```
> nano app/app/.env

SECRET_KEY="ohhhowsecret"
DEBUG="true"
POSTGRES_DB="postgres"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_HOST="db"
POSTGRES_PORT="5432"
```
3. запустите докер
```
> cd ../../
> docker-compose build
> docker-compose up
```
4. переходим на [0.0.0.0:80](http://0.0.0.0:8000) <br> <br>
***чтобы остановить работу докера нажмите Ctrl+C***

## 💣 фичиии!!!
### 1. Импортировать товары и категории:
**/imports** - POST-запрос<br><br>
```
curl -H "Content-Type: application/json" --request POST --data '{
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": null
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }'  http://127.0.0.1:8000/imports
```
<br><br>
### 2. Удалить объект по id:
**/delete/$id** - DELETE-запрос
```
curl -X DELETE https://slight-1933.usr.yandex-academy.ru/delete/069cb8d7-bbdd-47d3-ad8f-82ef4c269df1
```
<br><br>

<br><br>
### 3. Показать всю информацию об объекте с дочерними объектами для категорий:
**/nodes/$id** - GET-запрос
```
curl --request GET https://slight-1933.usr.yandex-academy.ru/nodes/069cb8d7-bbdd-47d3-ad8f-82ef4c269df1
```
<br><br>

<br><br>
### 4. Показать все версии обновленных товаров за 24 от указанной даты включительно:
**/sales?date=&date** - GET-запрос
```
curl --request GET https://slight-1933.usr.yandex-academy.ru/sales?date=2022-02-01T15:00:00.000Z
```
<br><br>
<br><br>
### 5. Показать историю обновлений объекта. Можно указать временные рамки. Можно и не указывать. Хотя я бы указал. 
**/node/$id/statistic?dateStart=$dateStart&dateEnd=$dateEnd** - GET-запрос
```
curl --request GET https://slight-1933.usr.yandex-academy.ru/node/069cb8d7-bbdd-47d3-ad8f-82ef4c269df1/statistic?dateStart=2022-02-01T10:00:00.000Z&dateEnd=2022-02-01T15:00:00.000Z
```
<br><br>

Я, конечно, изрядно потрудился над этим, но деплоить нормально научиться не успел, сорри.
