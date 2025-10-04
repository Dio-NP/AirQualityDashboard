from __future__ import annotations
from typing import Optional

try:
    from harmony import Client
except Exception:  # pragma: no cover
    Client = None


def subset_harmony(collection: str, bbox: Optional[str], time_range: Optional[str], output: str) -> dict:
    if Client is None:
        raise RuntimeError("harmony-py not installed")
    client = Client()
    req = client.submit(
        collection=collection,
        spatial=bbox,
        temporal=time_range,
        format="netcdf4"
    )
    resp = client.result_json(req)
    # Download first item
    hrefs = [i.get('href') for i in resp.get('links', []) if i.get('rel') == 'data']
    if not hrefs:
        return {"downloaded": 0}
    first = hrefs[0]
    client.download_url(first, output)
    return {"downloaded": 1, "file": output}
