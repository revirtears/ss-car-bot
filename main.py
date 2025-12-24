from asyncio import run
from src.core.runner import BotRunner


if __name__ == '__main__':
    runner = BotRunner()

    try:
        run(runner.run())
    except KeyboardInterrupt: pass
