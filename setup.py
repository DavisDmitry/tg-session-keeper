from setuptools import setup
from typing import List, Tuple

# import session_keeper


NAME = 'tg-session-keeper'
DESCRIPTION = 'Консольная утилита для хранения Telegram-сессий.'
URL = 'https://github.com/DavisDmitry/tg-session-keeper'
EMAIL = 'dmitrydavis@protonmail.com'
AUTHOR = 'Dmitry Davis'
REQUIRES_PYTHON = '>=3.7'
VERSION = '0.1.0'


def parse_long_description() -> Tuple[str, str]:
    try:
        with open('README.md') as file:
            return file.read(), 'text/markdown'
    except FileNotFoundError:
        return DESCRIPTION, 'text/plain'


LONG_DESCRIPTION, LONG_DESCRIPTION_CONTENT_TYPE = parse_long_description()


def parse_requirements() -> List[str]:
    with open('requirements.txt') as file:
        return file.read().splitlines()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=['session_keeper'],
    entry_points={
        'console_scripts': ['session-keeper=session_keeper:main']
    },
    install_requires=parse_requirements(),
    include_package_data=False,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities'
    ]
)
