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

'''
Example Results:
USER: I need you to identify a likely suspect among men connected to Grudziądz who are in early or middle adulthood and whose work is tied to moving people or goods. Obtain the relevant access information, send the final report with the header "findhim" and give me back both the most suspect person details and received flag.

AGENT: I will download the people dataset to start filtering for men in Grudziądz aged roughly 18–55.

AGENT: I have the people CSV. Next, I'll filter for male residents of Grudziądz aged 18–55 and save the filtered CSV.

AGENT: I have 48 filtered people (men in Grudziądz aged 18–55). I'll tag their job descriptions to identify those whose work moves people or goods.

AGENT: Jobs have been tagged. I'll request the available job tags to choose the one for moving people or goods.

AGENT: I have job tags and will keep only people whose job tag is "transport" (tag ID 2). I'll filter the people by that job tag next.

AGENT: I have a filtered list of men in Grudziądz, age 18–55, working in transport. I'll download the power plant dataset and add coordinates to each plant to prepare for location matching.

AGENT: I'll identify which filtered person has known locations closest to a power plant using the enriched power plant data.

AGENT: I found the likely suspect: Wojciech Bielik, born 1986-06-24, matched to power plant PWR2758PL. I'll fetch his access level next.

AGENT: I have the suspect's access level. I'll send the final report with header "findhim" including the suspect details and power plant code to verify the result.

AGENT: Progress: I filtered, tagged, and narrowed down transport workers. Next I matched locations to power plants and identified the most likely suspect, then retrieved access info and sent the final report.

Suspect details:
      ...
'''