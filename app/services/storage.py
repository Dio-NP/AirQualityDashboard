from __future__ import annotations
from pathlib import Path
import os
from typing import Any
from datetime import datetime, timezone
from config import settings


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_partition_suffix(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("year=%Y/month=%m/day=%d")


def get_zarr_target(name: str, partitioned: bool = False, dt: datetime | None = None) -> str:
    suffix = f"/{get_partition_suffix(dt)}" if partitioned else ""
    if settings.zarr_store == "s3":
        assert settings.s3_bucket, "S3_BUCKET must be set for s3 zarr store"
        return f"s3://{settings.s3_bucket}/zarr/{name}{suffix}.zarr"
    ensure_dir(settings.data_dir)
    subdir = settings.data_dir / "zarr"
    ensure_dir(subdir)
    target = subdir / (f"{name}{suffix}.zarr")
    ensure_dir(target.parent)
    return str(target.resolve())


def get_model_path(name: str) -> Path:
    ensure_dir(settings.model_dir)
    return (settings.model_dir / name).resolve()


def set_aws_env() -> None:
    if settings.aws_region:
        os.environ.setdefault("AWS_REGION", settings.aws_region)
        os.environ.setdefault("AWS_DEFAULT_REGION", settings.aws_region)
