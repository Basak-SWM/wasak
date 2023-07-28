from pydantic_settings import BaseSettings, SettingsConfigDict


class ClovaSpeechConfigs(BaseSettings):
    clova_secret_key: str
    clova_stt_target_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


clova_speech_config = ClovaSpeechConfigs()
