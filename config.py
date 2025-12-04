from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN: str
    LOGGING_LEVEL: str
    MAIN_ADMINS: list[int]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


