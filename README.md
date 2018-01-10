# plainrest
Тестовый сервер тестового скоринга.

В качестве хранилища используется Tarantool.

### Запуск сервера
Пример: `python api.py --log=server.log --port=8080`

* `port` - порт, по-умолчанию 8080
* `log` - путь к логам сервера (если не указан, лог пишется в stdout)
* `tarantool_host` - хост Tarantool (Тарантул работает хранилищем)
* `tarantool_port` - порт Tarantool
* `tarantool_login` - логин для Tarantool
* `tarantool_passwotd` - пароль для Tarantool


### Запуск тестов

`python test.py`

Для тестов с хранилищем нужно, чтобы в системе был установлен Docker. 

Перед запуском тестов необходимо выполнить `docker-compose up -d` 