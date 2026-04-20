from .agent import run_agent
from .hub_client import HubClient
from .tools import RECON_TOOLS, make_recon_handlers

INSTRUCTIONS = """
You are a warehouse recon agent. Your task is to gather all data needed to create delivery orders for a list of target cities.

Follow these steps using the available tools:

1. Call query_database("SHOW TABLES") to discover all tables.
2. Before querying any table, ALWAYS run SHOW CREATE TABLE <name> first to learn the exact column names.
   Never assume column names — use only what the schema reveals.
3. Find the numeric destination_id for each target city from the destinations table.
   City names are stored with capital first letter (e.g. "Opalino"). Use exact casing or LOWER().
   The table has 40 rows total but the default limit is 30 — use LIMIT/OFFSET to get all rows.
4. Find which role corresponds to transport staff from the roles table.
5. Find a user with the transport role from the users table.
   Use SHOW CREATE TABLE users first to get exact column names, then query using those names.
   You need their login, birthday, and user_id (or whatever the primary key column is named).
6. For each target city, call generate_signature with the transport user's login and birthday and the city's destination_id.

When done, respond with a single JSON object (no markdown, no extra text) structured as:
{
  "creator_id": <int>,
  "cities": {
    "<city_name>": {
      "destination_id": <int>,
      "signature": "<sha1>"
    },
    ...
  }
}
""".strip()


async def run_recon(target_cities: list[str]) -> str:
    hub = HubClient()
    handlers = make_recon_handlers(hub)

    user_message = (
        f"Gather all data required to create orders for these cities: {', '.join(target_cities)}.\n"
        "Return the result as a JSON object as described in your instructions."
    )

    return await run_agent(
        instructions=INSTRUCTIONS,
        user_message=user_message,
        tools=RECON_TOOLS,
        handlers=handlers,
    )
