from dotenv import load_dotenv

from src.agents.findhim_agent import FindHimAgent
from src.config.settings import Settings


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    agent = FindHimAgent(settings)

    # user_prompt = 'I am looking for a man aged 20 to 40, born in Grudziądz, whose work is related to transport. Use the available datasets and tools to identify the most likely suspect connected to a power plant, determine his access level, and at the end send a message with this person data using the header "findhim". Finally, give me the flag that you received.'
    # user_prompt = 'I need you to identify a likely suspect among men connected to Grudziądz who are in early or middle adulthood and whose work is tied to moving people or goods. Use the available data sources to narrow the group, determine which person is most likely linked to a power plant, obtain the relevant access information, send the final report with the header "findhim" and give me back both the most suspect person details and received flag.'
    user_prompt = 'I need you to identify a likely suspect among men connected to Grudziądz who are in early or middle adulthood and whose work is tied to moving people or goods. Obtain the relevant access information, send the final report with the header "findhim" and give me back both the most suspect person details and received flag.'
    agent.run(user_prompt=user_prompt)

if __name__ == '__main__':
    main()
