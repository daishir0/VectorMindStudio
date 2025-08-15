import re

_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = _FILENAME_SAFE.sub("-", name)
    # 禁止先頭ピリオド
    if name.startswith('.'):
        name = name.lstrip('.')
    return name or "file"

