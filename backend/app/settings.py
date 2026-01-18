from pydantic_settings import BaseSettings
from functools import lru_cache
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    db_driver_async: str = "postgresql+asyncpg"
    db_driver_sync: str = "postgresql"
    db_username: str = "mattilda"
    db_password: str = "mattilda"
    db_hostname: str = "db"
    db_port: int = 5432
    db_name: str = "mattilda"
    debug: bool = True

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername=self.db_driver_async,
            username=self.db_username,
            password=self.db_password,
            host=self.db_hostname,
            port=self.db_port,
            database=self.db_name,
        )

    @property
    def database_url_sync(self) -> URL:
        return URL.create(
            drivername=self.db_driver_sync,
            username=self.db_username,
            password=self.db_password,
            host=self.db_hostname,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
