import json

from .agent import run_agent
from .hub_client import HubClient
from .tools import ORDERS_TOOLS, make_orders_handlers

INSTRUCTIONS = """
You are a warehouse orders agent. Your job is to create and fill all delivery orders for a set of cities, then submit them for verification.

You are given:
- recon_data: JSON with creator_id and per-city destination_id + signature
- city_needs: JSON mapping city name to required items and quantities

For each city in city_needs:
1. Call create_order with the city's destination_id, creator_id, signature, and a descriptive title.
2. Call append_items with the returned order_id and the city's items dict.

After all cities are processed, call submit_done to finalize.
The flag will be returned by submit_done on success.

Important:
- Process every city — do not skip any.
- Use exact item quantities from city_needs.
- Call submit_done only once, after all orders are created and filled.
""".strip()


async def run_orders(recon_result: str, city_needs: dict) -> str:
    hub = HubClient()
    handlers = make_orders_handlers(hub)

    user_message = (
        f"Recon data:\n{recon_result}\n\n"
        f"City needs:\n{json.dumps(city_needs, ensure_ascii=False, indent=2)}\n\n"
        "Create all orders, fill them with the correct items, then call submit_done."
    )

    return await run_agent(
        instructions=INSTRUCTIONS,
        user_message=user_message,
        tools=ORDERS_TOOLS,
        handlers=handlers,
    )
