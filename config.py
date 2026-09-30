# External imports 
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secret string prevents accidental logging of the value by masking it unless .get_secret_value() is used
class Settings(BaseSettings):
    DISCORD_TOKEN: SecretStr 
    DATABASE_URL: str
    ADMIN_API_KEY: SecretStr

    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    # Looks at .env upon startup and loads variables into memory
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Settings is used to call the secret variables
settings = Settings(**{})
