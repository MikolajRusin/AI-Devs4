from src.agent import run_agent
from src.logger import logger


def main():
    logger.start('Start Agent')

    user_message = 'Set railway route X-01 as open. Start by calling the help action.'
    logger.query(user_message)

    final_message = run_agent(user_message)

    logger.response(final_message)


if __name__ == '__main__':
    main()