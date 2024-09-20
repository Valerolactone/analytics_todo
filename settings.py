from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_initdb_root_username: str = Field(..., env="MONGO_INITDB_ROOT_USERNAME")
    mongo_initdb_root_password: str = Field(..., env="MONGO_INITDB_ROOT_PASSWORD")
    mongo_host: str = Field(..., env="MONGO_HOST")
    mongo_port: int = Field(..., env="MONGO_PORT")
    mongo_db_name: str = Field(..., env="MONGO_DB_NAME")

    debug: bool = Field(False, env="DEBUG")

    kafka_bootstrap_servers: str = Field(..., env="KAFKA_BOOTSTRAP_SERVERS")

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@{self.mongo_host}:{self.mongo_port}"


settings = Settings()
