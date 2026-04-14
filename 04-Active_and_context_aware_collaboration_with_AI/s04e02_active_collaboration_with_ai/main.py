from src.agent import run_agent

TASK = (
    'Program the wind turbine scheduler using the windpower API.\n'
    '\n'
    'Call run_windpower_session() — it handles everything atomically.\n'
    'Report the flag from the done.message field in the response.\n'
    'If done.code is negative, call it again.\n'
)


def main():
    result = run_agent(TASK)
    print(f'\n[main] result = {result}')


if __name__ == '__main__':
    main()
