# Telegram Session Keeper
[![PyPi Package Version](https://img.shields.io/pypi/v/tg-session-keeper?style=flat-square)](https://pypi.org/project/tg-session-keeper)
[![MIT License](https://img.shields.io/pypi/l/tg-session-keeper?style=flat-square "MIT License")](https://pypi.org/project/tg-session-keeper "MIT License")
[![Supported python versions](https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9-blue?style=flat-square&logo=python)](https://www.python.org/)
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
usage: session-keeper [-h] [--filename FILENAME]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  path to a sessions file
```
### Команды
```
add <PHONE>        создать Telegram-сессию
remove <NUMBER>    удалить сессию
list               список сессий
get <NUMBER>       посмотреть последнее сообщение от Telegram
exit               выйти из программы
```
## Скриншоты
### Список сессий
![Список сессий](https://github.com/DavisDmitry/tg-session-keeper/blob/master/img/sessions.png)
### Пример сообщения от Telegram
![Сообщение от Telegram](https://github.com/DavisDmitry/tg-session-keeper/blob/master/img/message.png)
