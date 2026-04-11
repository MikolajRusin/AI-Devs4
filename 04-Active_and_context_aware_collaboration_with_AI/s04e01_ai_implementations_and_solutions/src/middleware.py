_INTERNAL_KEYS = {'apikey', 'task'}


def _strip_internal(obj):
    if isinstance(obj, dict):
        return {k: _strip_internal(v) for k, v in obj.items() if k not in _INTERNAL_KEYS}
    if isinstance(obj, list):
        return [_strip_internal(item) for item in obj]
    return obj


def on_tool_call(result: dict) -> dict:
    return _strip_internal(result)
