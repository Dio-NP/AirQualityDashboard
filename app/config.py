from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    zarr_store: str = Field(default="local", alias="ZARR_STORE")  # local or s3
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    aws_region: str | None = Field(default=None, alias="AWS_REGION")

    openaq_base_url: str = Field(default="https://api.openaq.org/v2", alias="OPENAQ_BASE_URL")
    airnow_api_key: str | None = Field(default=None, alias="AIRNOW_API_KEY")
    openweather_api_key: str | None = Field(default=None, alias="OPENWEATHER_API_KEY")
    earthdata_username: str | None = Field(default=None, alias="EARTHDATA_USERNAME")
    earthdata_password: str | None = Field(default=None, alias="EARTHDATA_PASSWORD")

    # TEMPO versions
    tempo_version_standard: str = Field(default="V04", alias="TEMPO_VERSION_STANDARD")
    tempo_version_nrt: str = Field(default="V02", alias="TEMPO_VERSION_NRT")

    # Caching
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    model_dir: Path = Field(default=Path("./models"), alias="MODEL_DIR")

    # Notifications
    sendgrid_api_key: str | None = Field(default=None, alias="SENDGRID_API_KEY")
    email_from: str | None = Field(default=None, alias="EMAIL_FROM")
    twilio_sid: str | None = Field(default=None, alias="TWILIO_SID")
    twilio_token: str | None = Field(default=None, alias="TWILIO_TOKEN")
    twilio_from: str | None = Field(default=None, alias="TWILIO_FROM")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
