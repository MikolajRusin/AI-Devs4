import json

from .hub_client import HubClient
from .task_spec import TaskSpec

TRANSLATION_TABLE = str.maketrans({
    'ą': 'a',
    'ć': 'c',
    'ę': 'e',
    'ł': 'l',
    'ń': 'n',
    'ó': 'o',
    'ś': 's',
    'ź': 'z',
    'ż': 'z',
})

EXTRACTOR_INSTRUCTIONS = """
You are a data extraction specialist. Read Natan's three note files and output a single JSON object.

## Output format

Output ONLY this JSON structure, nothing else:

{
  "cities": {
    "<cityname>": {"<item>": <qty>, ...},
    ...
  },
  "persons": {
    "<filename>": {"name": "<Full Name with Polish chars>", "city": "<cityfilename>"},
    ...
  },
  "goods": {
    "<item>": ["<sellingcity>", ...],
    ...
  }
}

## Rules

- cities keys: lowercase, no Polish characters, no spaces (e.g. "domatowo", "brudzewo")
- cities values: item names MUST be a single word, singular nominative, lowercase, no Polish characters.
  Extract the ROOT NOUN only — NEVER use multi-word phrases:
  * "butelek wody" → "woda"  (NOT "butelka_wody", NOT "butelka wody")
  * "porcji wołowiny" → "wolowina"  (NOT "porcja_wolowiny")
  * "porcji kurczaka" → "kurczak"  (NOT "porcja_kurczaka")
  * "worków ryżu" → "ryz"
  * "mlotki" → "mlotek"
  * "kilofy" → "kilof"
  * "wiertarek" → "wiertarka"
  * "lopat" → "lopata"
  * "ziemniakow" → "ziemniak"
- persons keys: EXACTLY firstname+surname concatenated, ALL lowercase, no Polish characters, no spaces (e.g. "natanrams", "damiankroll"). NEVER include spaces or separators.
- persons "name": preserve Polish characters exactly as the person is known. Use the FULL name (first name + surname) — never just a surname alone.
- persons "city": city filename (lowercase, no Polish chars)
- goods keys: item name, single word, singular nominative, lowercase, no Polish characters (same root-noun rules as cities values)
- goods values: ONLY cities that appear on the LEFT side of -> in transakcje.txt for that item. Cities on the RIGHT side are buyers — NEVER include buyers as sellers. Example: "Opalino -> wołowina -> Darzlubie" means ONLY Opalino sells wołowina — Darzlubie is a buyer, NOT a seller.

## Persons rules

- For persons, some people are referred to only by surname in some sentences and first name in other sentences. Combine them carefully to extract the FULL name (first name + surname).
  * If a sentence says "Kisiel ma do mnie dzwonic" and another says "Rafał oddzwonil wieczorem" in the same context about Brudzewo, combine to "Rafał Kisiel".
  * If the text mentions "Konkel" and also "Lena pilnuje tam handlu" about Karlinkowo, combine to "Lena Konkel".
- Always use the FULL name for both the filename key (concatenated, no Polish chars) and the "name" field (with Polish chars preserved).

## Sources

- workspace/notes/ogłoszenia.txt — city demands
- workspace/notes/rozmowy.txt — persons and their cities
- workspace/notes/transakcje.txt — format: Seller -> item -> Buyer (left = seller)

## CRITICAL: Do not cross-pollinate data between files

- "cities" values come EXCLUSIVELY from ogłoszenia.txt. ONLY include items with actual positive quantities from that file. Do NOT add items that appear in transakcje.txt. Do NOT add items with quantity 0.
- "goods" values come EXCLUSIVELY from transakcje.txt. ONLY include items that actually appear in transakcje.txt. Do NOT invent items like "woda" that don't appear as transaction items.
"""

REVIEWER_INSTRUCTIONS = """
You are a strict data reviewer for the filesystem task.
You receive an extracted JSON object and must verify it against the three note files.
Treat "cities" and "persons" as locked unless the verifier feedback explicitly says they are wrong.
Your main job is to correct the "goods" section.

Read ALL three source files again before answering:
- workspace/notes/ogłoszenia.txt
- workspace/notes/rozmowy.txt
- workspace/notes/transakcje.txt

Return ONLY a corrected JSON object in exactly this shape:
{
  "cities": {
    "<cityname>": {"<item>": <qty>, ...}
  },
  "persons": {
    "<filename>": {"name": "<Full Name>", "city": "<cityfilename>"}
  },
  "goods": {
    "<item>": ["<sellingcity>", ...]
  }
}

Critical checks before you answer:
- Every city and item filename key must be lowercase ASCII with no Polish characters.
- Every good sold in transakcje.txt must exist in goods.
- Seller cities come ONLY from the LEFT side of "Seller -> item -> Buyer".
- If a good is sold by multiple cities, include every seller exactly once.
- Keep item names as the singular root noun.
- DO NOT cross-pollinate data between sections.
- "cities" must use ONLY ogłoszenia.txt.
- "persons" must use ONLY rozmowy.txt.
- "goods" must use ONLY transakcje.txt.
- If the provided JSON already has a correct value, keep it unchanged.
- Only fix actual mistakes.
- Re-read your final JSON against the source files before returning it.
"""


def _ascii_slug(value: str) -> str:
    return value.lower().translate(TRANSLATION_TABLE).replace(' ', '_')


def normalize_extracted(data: dict) -> dict:
    cities = {
        city: {_ascii_slug(item): qty for item, qty in items.items()}
        for city, items in data.get('cities', {}).items()
    }
    persons = {
        filename: {
            **person,
            'city': _ascii_slug(person['city']),
        }
        for filename, person in data.get('persons', {}).items()
    }
    goods: dict[str, list[str]] = {}
    for item, sellers in data.get('goods', {}).items():
        normalized_item = _ascii_slug(item)
        normalized_sellers = [_ascii_slug(city) for city in sellers]
        goods[normalized_item] = list(dict.fromkeys(normalized_sellers))
    return {
        'cities': cities,
        'persons': persons,
        'goods': goods,
    }


def lock_reviewed_sections(extracted: dict, reviewed: dict) -> dict:
    reviewed['cities'] = extracted['cities']
    reviewed['persons'] = extracted['persons']
    return reviewed


def build_filesystem(data: dict, hub: HubClient) -> dict:
    print(f"[build] reset: {hub.reset()}")

    for path in ('/miasta', '/osoby', '/towary'):
        print(f'[build] mkdir {path}: {hub.create_dir(path)}')

    operations = []

    for city, items in data['cities'].items():
        operations.append({
            'action': 'createFile',
            'path': f'/miasta/{city}',
            'content': json.dumps(items, ensure_ascii=False, separators=(',', ':')),
        })

    for filename, person in data['persons'].items():
        operations.append({
            'action': 'createFile',
            'path': f'/osoby/{filename}',
            'content': f"{person['name']}\n[{person['city']}]({person['city']})",
        })

    for item, sellers in data['goods'].items():
        operations.append({
            'action': 'createFile',
            'path': f'/towary/{item}',
            'content': '\n'.join(f'[{city}]({city})' for city in sellers),
        })

    batch_result = hub.batch(operations)
    print(f'[build] batch: {batch_result}')
    return hub.done()


FILESYSTEM_SPEC = TaskSpec(
    name='filesystem',
    extractor_instructions=EXTRACTOR_INSTRUCTIONS,
    reviewer_instructions=REVIEWER_INSTRUCTIONS,
    normalize_extracted=normalize_extracted,
    lock_reviewed=lock_reviewed_sections,
    build=build_filesystem,
)
