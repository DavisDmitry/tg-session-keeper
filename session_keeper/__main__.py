import asyncio

from .cli import main as cli


def main() -> None:
    asyncio.run(cli())


if __name__ == '__main__':
    main()
