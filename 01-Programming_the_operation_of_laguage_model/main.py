from dotenv import load_dotenv

from src.agents.findhim_agent import FindHimAgent
from src.config.settings import Settings


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    agent = FindHimAgent(settings)

    user_prompt = 'I am looking for a man aged 20 to 40, born in Grudziądz, whose work is related to transport. Use the available datasets and tools to identify the most likely suspect connected to a power plant, determine his access level, and at the end send a message with this person data using the header "findhim". Finally, give me the flag that you received.'
    agent.run(user_prompt=user_prompt)

if __name__ == '__main__':
    main()
