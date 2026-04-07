import json

from .chat_api import chat_responses, extract_response_text
from .config import QUERY_REWRITE_MODEL
from .shop_service import (
    cities_for_item_queries,
    find_city_matches,
    intersection_for_item_queries,
    items_in_city,
    load_data,
    search_items,
)


MAX_OUTPUT_BYTES = 500


def _clip_output(text: str) -> str:
    encoded = text.encode('utf-8')
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return text

    clipped = encoded[: MAX_OUTPUT_BYTES - 3].decode('utf-8', errors='ignore').rstrip()
    return f'{clipped}...'


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _rewrite_query_with_model(query: str, dataset) -> list[str]:
    print(f'[rewrite] input_query={query}')
    response_format = {
        "type": "json_schema",
        "name": "query_rewrite",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["queries"],
            "additionalProperties": False,
        },
    }
    instructions = (
        "Convert one natural-language request into up to 3 short catalog search queries for concrete parts or components. "
        "Do not paraphrase the whole requested product. "
        "Break the request into component-level items that could exist in an electronics or technical parts catalog. "
        "Use short noun phrases with useful specs when present. "
        "Return only JSON."
    )
    user_message = (
        f"Request: {query}\n"
        "Rules:\n"
        "- Return parts/components, not a rewritten sentence.\n"
        "- Avoid repeating the full original product name.\n"
        "- Prefer searchable catalog phrases.\n"
        "- Maximum 3 queries.\n"
    )

    try:
        response = chat_responses(
            model=QUERY_REWRITE_MODEL,
            input=user_message,
            instructions=instructions,
            response_format=response_format,
            timeout=50,
        )
        payload = json.loads(extract_response_text(response))
    except Exception as exc:
        print(f'[rewrite] failed error={type(exc).__name__}: {exc}')
        print(f'[rewrite] fallback_to_original={query}')
        return [query]

    rewritten = payload.get('queries', [])
    if not isinstance(rewritten, list):
        print(f'[rewrite] invalid_payload={payload}')
        return [query]

    cleaned = [item.strip() for item in rewritten if isinstance(item, str) and item.strip()]
    result = _dedupe(cleaned)[:3] or [query]
    print(f'[rewrite] rewritten_queries={result}')
    return result


def _normalize_queries(queries: list[str], dataset) -> list[str]:
    print(f'[normalize] raw_queries={queries}')
    matched_queries: list[str] = []
    for query in queries:
        candidate = query.strip()
        if not candidate:
            continue
        if search_items(candidate, dataset):
            print(f'[normalize] direct_match={candidate}')
            matched_queries.append(candidate)
            continue

        rewritten_queries = _rewrite_query_with_model(candidate, dataset)
        for rewritten_query in rewritten_queries:
            if search_items(rewritten_query, dataset):
                print(f'[normalize] rewritten_match source={candidate} match={rewritten_query}')
                matched_queries.append(rewritten_query)
    result = _dedupe(matched_queries)
    print(f'[normalize] normalized_queries={result}')
    return result


def search_item(city: str | None = None, queries: list[str] | None = None) -> str:
    print(f'[search_item] city={city} queries={queries}')
    dataset = load_data()
    item_queries = _normalize_queries(queries or [], dataset)

    if city:
        matched_cities = find_city_matches(city, dataset)
        print(f'[search_item] matched_cities={matched_cities}')
        if not matched_cities:
            return 'CITY_NOT_FOUND'
        city_name = matched_cities[0]
        city_items = items_in_city(city_name, dataset)
        if not city_items:
            return f'CITY:{city_name}; ITEMS:BRAK'
        preview = ' | '.join(city_items[:8])
        suffix = '' if len(city_items) <= 8 else f' | +{len(city_items) - 8}'
        result = _clip_output(f'CITY:{city_name}; ITEMS:{preview}{suffix}')
        print(f'[search_item] result={result}')
        return result

    if not item_queries:
        print('[search_item] no_item_queries')
        return 'NO_MATCH'

    if len(item_queries) == 1:
        per_query = cities_for_item_queries(item_queries[:1], dataset)
        print(f'[search_item] per_query={per_query}')
        if not per_query:
            return 'NO_MATCH'
        query = next(iter(per_query))
        cities = per_query[query]
        preview = ', '.join(cities[:10])
        suffix = '' if len(cities) <= 10 else f', +{len(cities) - 10}'
        result = _clip_output(f'ITEM:{query}; CITIES:{preview}{suffix}')
        print(f'[search_item] result={result}')
        return result

    common_cities = intersection_for_item_queries(item_queries[:3], dataset)
    print(f'[search_item] common_cities={common_cities}')
    if not common_cities:
        searched = ' | '.join(item_queries[:3])
        result = _clip_output(f'ITEMS:{searched}; CITIES:BRAK')
        print(f'[search_item] result={result}')
        return result

    searched = ' | '.join(item_queries[:3])
    preview = ', '.join(common_cities[:10])
    suffix = '' if len(common_cities) <= 10 else f', +{len(common_cities) - 10}'
    result = _clip_output(f'ITEMS:{searched}; CITIES:{preview}{suffix}')
    print(f'[search_item] result={result}')
    return result


def search_from_params(params: str | dict) -> str:
    print(f'[search_from_params] raw_params={params}')
    if isinstance(params, dict):
        payload = params
    else:
        try:
            payload = json.loads(params)
        except json.JSONDecodeError:
            print('[search_from_params] invalid_json')
            return 'INVALID_PARAMS'

    if not isinstance(payload, dict):
        print(f'[search_from_params] invalid_payload_type={type(payload)}')
        return 'INVALID_PARAMS'

    city = payload.get('city')
    queries = payload.get('queries')
    print(f'[search_from_params] city={city} queries={queries}')

    if city is not None and not isinstance(city, str):
        print('[search_from_params] invalid_city')
        return 'INVALID_PARAMS'
    if queries is not None and (
        not isinstance(queries, list) or not all(isinstance(query, str) for query in queries)
    ):
        print('[search_from_params] invalid_queries')
        return 'INVALID_PARAMS'
    if not city and not queries:
        print('[search_from_params] missing_city_and_queries')
        return 'INVALID_PARAMS'

    return search_item(city=city, queries=queries)
