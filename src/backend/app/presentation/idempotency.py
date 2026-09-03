import hashlib
import json
from collections.abc import Mapping

type JsonPayload = Mapping[str, object]


def request_fingerprint(payload: JsonPayload) -> str:
    encoded = json.dumps(payload, sort_keys=True,
                         separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
