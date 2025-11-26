import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret_key_123")
    MONGO_URI = os.environ.get("MONGO_URI")