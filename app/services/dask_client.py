from __future__ import annotations
from typing import Optional

try:
    from dask.distributed import Client, LocalCluster  # type: ignore
except Exception:  # pragma: no cover
    Client = None
    LocalCluster = None


def get_dask_client(scheduler: Optional[str] = None):
    if Client is None:
        return None
    if scheduler:
        return Client(scheduler)
    cluster = LocalCluster(n_workers=2, threads_per_worker=2)
    return Client(cluster)
