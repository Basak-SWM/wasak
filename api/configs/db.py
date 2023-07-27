from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfigs(BaseSettings):
    db_username: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    def get_full_url(self) -> str:
        return f"mysql+pymysql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = DatabaseConfigs()
