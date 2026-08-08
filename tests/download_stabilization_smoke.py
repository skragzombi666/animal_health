from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "custom_components" / "animal_health" / "download_stabilization.py"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    ast.parse(text)
    assert "tokens.get(token)" in text
    assert "tokens.pop(token, None)" in text
    assert "timedelta(minutes=15)" in text
    assert 'feature_api._consume_transfer_token = _consume_transfer_token' in text
    assert "record[\"expires_at\"] = now + _TOKEN_RETRY_WINDOW" in text
    assert "tokens.pop(token, None)\n    if record is None" not in text
    print("download stabilization smoke test passed")


if __name__ == "__main__":
    main()
