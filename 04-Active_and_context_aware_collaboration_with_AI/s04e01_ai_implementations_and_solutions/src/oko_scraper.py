import json

import html_to_markdown
import requests
from bs4 import BeautifulSoup

from .chat_api import chat_responses
from .config import OKO_BASE_URL, OKO_LOGIN, OKO_PASSWORD, SCRAPE_MODEL, AI_DEVS_HUB_API_KEY


SCRAPER_INSTRUCTIONS = (
    'You are a markdown parser. Extract all records from the provided markdown page. '
    'The content may be in Polish. '
    'For each record extract: its unique identifier found in the link URLs, '
    'the title, status, and a short excerpt of any description text (max 100 characters). '
    'Return ONLY a raw JSON array — no markdown, no code fences — '
    'a list of objects with fields: id, title, status, excerpt.'
)


def _login() -> requests.Session:
    session = requests.Session()
    response = session.post(
        f'{OKO_BASE_URL}',
        data={
            'action': 'login',
            'login': OKO_LOGIN,
            'password': OKO_PASSWORD,
            'access_key': AI_DEVS_HUB_API_KEY,
        }
    )
    print(response)
    response.raise_for_status()
    return session


def _fetch_page(session: requests.Session, path: str) -> str:
    response = session.get(f'{OKO_BASE_URL}{path}')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    main = soup.find('main')
    target = main if main else soup
    for tag in target(['script', 'style', 'meta', 'head', 'nav', 'footer']):
        tag.decompose()
    for tag in target.find_all('a', href='/'):
        tag.decompose()
    return html_to_markdown.convert(str(target))


def _extract_ids_with_llm(page_text: str) -> list[dict]:
    print(SCRAPE_MODEL)
    response = chat_responses(
        model=SCRAPE_MODEL,
        input=page_text,
        instructions=SCRAPER_INSTRUCTIONS,
        tools=[],
    )
    output_text = ''
    for item in response.get('output', []):
        for content in item.get('content', []):
            text = content.get('text')
            if isinstance(text, str) and text:
                output_text += text

    text = output_text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1]
        text = text.rsplit('```', 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f'[scraper] json parse failed, raw output: {output_text[:300]}')
        return []


def scrape_page(path: str, record_id: str | None = None) -> list[dict] | str:
    print(f'[scraper] logging in')
    session = _login()

    if record_id:
        full_path = f'{path}/{record_id}'
        print(f'[scraper] fetching detail path={full_path}')
        return _fetch_page(session, full_path)

    print(f'[scraper] fetching list path={path}')
    page_text = _fetch_page(session, path)
    print(f'[scraper] extracting records with llm')
    records = _extract_ids_with_llm(page_text)
    print(f'[scraper] found {len(records)} records')
    return records
