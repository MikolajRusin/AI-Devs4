import asyncio
import json
import os

from src.recon_agent import run_recon
from src.orders_agent import run_orders

WORKSPACE = os.path.join(os.path.dirname(__file__), 'workspace')
CITIES_FILE = os.path.join(WORKSPACE, 'food4cities.json')


async def main():
    with open(CITIES_FILE, encoding='utf-8') as f:
        city_needs: dict = json.load(f)

    target_cities = list(city_needs.keys())

    print('=== AGENT 1: RECON ===')
    recon_result = await run_recon(target_cities)
    print(f'\n[main] Recon result:\n{recon_result}\n')

    print('=== AGENT 2: ORDERS ===')
    flag = await run_orders(recon_result=recon_result, city_needs=city_needs)
    print(f'\n[main] Flag: {flag}')


if __name__ == '__main__':
    asyncio.run(main())
