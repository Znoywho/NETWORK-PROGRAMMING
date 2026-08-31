import os 
from dotenv import load_dotenv
class Config:
    load_dotenv()
    DATABASE_URI = str(os.getenv("CARO_DB"))

print(Config.DATABASE_URI)

