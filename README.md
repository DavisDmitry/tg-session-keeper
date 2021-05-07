# Telegram Session Keeper
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tg-session-keeper?logo=python&style=flat-square)](https://python.org)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tg-session-keeper?style=flat-square)](https://pypi.org/project/tg-session-keeper)
[![PyPi Package Version](https://img.shields.io/pypi/v/tg-session-keeper?style=flat-square)](https://pypi.org/project/tg-session-keeper)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/DavisDmitry/tg-session-keeper/Tests/master?label=tests&style=flat-square)](https://github.com/DavisDmitry/tg-session-keeper/actions/workflows/tests.yml)
[![GitHub](https://img.shields.io/github/license/DavisDmitry/tg-session-keeper?style=flat-square)](https://github.com/DavisDmitry/tg-session-keeper/raw/master/LICENSE)
[![Telethon](https://img.shields.io/badge/Telethon-blue?style=flat-square)](https://github.com/LonamiWebs/Telethon)

Консольная утилита для хранения Telegram-сессий.

Я использую несколько аккаунтов Telegram. Большинство из них зарегистрированы на одноразовые номера. Для входа в аккаунт с другого устройства необходимо ввести одноразовый код, получить его по SMS возможности уже нет. Чтобы не потерять доступ, создана эта утилита. Она позволяет хранить сессии в зашифрованном виде и посмотреть последнее сообщение от Telegram, в котором указан код для аутентификации.
## Использование
### Установка
```
pip install tg-session-keeper
```
### Запуск
```
usage: __main__.py [-h] [--filename FILENAME] [--test]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  path to a sessions file
  --test               run keeper on test Telegram server
```
### Команды
```
add                создать Telegram-сессию
remove <NUMBER>    удалить сессию
list               список сессий
get <NUMBER>       посмотреть последнее сообщение от Telegram
exit               выйти из программы
```
## Скриншоты
### Список сессий
![Список сессий](https://github.com/DavisDmitry/tg-session-keeper/raw/master/img/sessions.png)
### Пример сообщения от Telegram
![Сообщение от Telegram](https://github.com/DavisDmitry/tg-session-keeper/raw/master/img/message.png)
