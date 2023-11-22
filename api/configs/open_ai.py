from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfigs(BaseSettings):
    open_ai_secret_key: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


open_ai_config = OpenAIConfigs()
