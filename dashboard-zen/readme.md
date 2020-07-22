# Дашборд "Взаимодействие пользователей с карточками Яндекс.Дзен"

Дашборд выполнен в двух вариантах: для запуска на локальной машине с применением библиотеки dash и в Tableau.  
Дашборд в Tableau Public размещён по ссылке: [public.tableau.com](https://public.tableau.com/profile/alyssa7686#!/vizhome/Zen_Dashboard/Dashboard1?publish=yes)

## Инструкция для запуска дашборда на локальной машине (в случае, когда есть доступ к базе данных и нужно периодически формировать дашборд для отчёта)
Должен быть установлен PostgreSQL:
```bash
sudo apt update  
sudo apt install postgresql postgresql-contrib  

sudo service postgresql start  
service postgresql status
```
### Подготовка базы данных
1. создать базу данных `zen`:
```bash
createdb zen --encoding='utf-8'
```
2. в консоли PostgreSQL подключиться к базе данных `zen`, создать пользователя и выйти:
```sql
\c zen
CREATE USER my_user WITH ENCRYPTED PASSWORD 'my_user_password';
\q
```
3. загрузить базу данных из бэкап-файла в консоли системы:
```bash
pg_restore -d zen zen.dump
```
4. в консоли PostgreSQL подключиться к базе данных `zen`:
```bash
\c zen
```
5. создать таблицу `dash_engagement`:
```SQL
CREATE TABLE dash_engagement (record_id SERIAL PRIMARY KEY,
							  dt TIMESTAMP,
							  item_topic VARCHAR(20),
							  event VARCHAR(20),
							  age_segment VARCHAR(20),
							  unique_users BIGINT);
```
6. создать таблицу `dash_visits`:
```SQL
CREATE TABLE dash_visits (record_id SERIAL PRIMARY KEY,
						  item_topic VARCHAR(20),
						  source_topic VARCHAR(20),
						  age_segment VARCHAR(20),
						  dt TIMESTAMP,
						  visits INT);
```
7. установить права пользователю:
```SQL
GRANT ALL PRIVILEGES ON TABLE dash_visits TO my_user;
GRANT ALL PRIVILEGES ON TABLE dash_engagement TO my_user;
GRANT USAGE, SELECT ON SEQUENCE dash_visits_record_id_seq TO my_user;
GRANT USAGE, SELECT ON SEQUENCE dash_engagement_record_id_seq TO my_user;
```
### Установка расписания и первый запуск
Файл пайплайна называется `zen_pipeline.py` и должен храниться на сервере в папке `/home/test_user/code/`.  
Чтобы он запускался каждый день в 3:15 утра по Москве, нужно:
1. создать папку `logs` в папке `/home/test_user/`
	```bash
	mkdir /home/test_user/logs
	```
2. Вызвать редактор расписания `cron`
	```bash
	crontab -e
	```
3. Дописать строку в конце файла
	>`15 3 * * * python -u -W ignore /home/test_user/code/zen_pipeline.py --start_dt=$(date +\%Y-\%m-\%d\ 03:15:00 -d "1 day ago") --end_dt=$(date +\%Y-\%m-\%d\ 03:15:00) >> /home/test_user/logs/zen_pipeline.log 2>&1`

После этого информация о работе пайплайна будет сохраняться в файле `/home/test_user/logs/zen_pipeline.log`.  
Необходимо запустить пайплайн для формирования необходимых таблиц базы данных.  
```bash
python .\zen_pipeline.py
```

### Использование

Теперь в любое время можно посмотреть dashboard запустив скрипт
```bash
python .\dashboard.py
```

И открыв в браузере сраницу с адресом написанным в строке 'Running on' (например, http://127.0.0.1:8050/)
