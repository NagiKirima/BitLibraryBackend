from pydantic_settings import BaseSettings
import dotenv
import os

dotenv.load_dotenv()

class Settings(BaseSettings):
    db_host: str = os.getenv('POSTGRES_HOST')
    db_port: str = os.getenv('POSTGRES_PORT')
    db_user: str = os.getenv('POSTGRES_USER')
    db_password: str = os.getenv('POSTGRES_PASSWORD')
    db_name: str = os.getenv('POSTGRES_DB')
    db_url: str = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    api_key: str = os.getenv('API_KEY')
    api_user: str = os.getenv('API_USER')
    api_password: str = os.getenv('API_PASSWORD')


settings = Settings()