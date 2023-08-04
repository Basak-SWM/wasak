from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Config(BaseSettings):
    audio_bucket_name: str
    aws_region: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = S3Config()
