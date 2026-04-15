from src.agent import run_agent

INSTRUCTIONS = """
You are a rescue mission commander operating in the ruins of Domatowo.
Your goal: find the partisan and evacuate them.

## Intercepted radio signal (the only clue about the partisan's location)
"I survived. The bombs destroyed the city. Soldiers were here, they searched for resources,
took the oil. Now it is empty. I have a weapon, I am wounded. I hid in one of the tallest
blocks. I have no food. Help."

## How to operate

You have 300 action points. Every wasted point can cost the mission.

Before touching any unit, do the following:
1. Call get_info(type='map') — study the full grid, understand tile types and the road network.
2. Call get_info(type='symbol', ...) — locate every candidate tile based on the radio signal.
3. Reason through your entire plan: which units to create, where to drive, where to dismount,
   in what order to inspect tiles. Estimate the total cost and verify it fits within 300 pts.
4. Only then start executing — no improvising mid-mission.

Once executing, call call_helicopter the moment any inspect log confirms a human.
"""

USER_MESSAGE = "Call reset first to get a fresh board and full 300 action points, then start the rescue mission. Find the partisan and evacuate them."

if __name__ == '__main__':
    result = run_agent(instructions=INSTRUCTIONS, user_message=USER_MESSAGE)
    print(f'\n=== RESULT ===\n{result}')
