import os

from dotenv import load_dotenv

# ===CHECK USING DOCKER===
IS_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"

if IS_DOCKER:
    DATABASE_URL = os.getenv("CARO_DB_DOCKER")
else:
    DATABASE_URL = os.getenv("OUT_CARO_DATABASE_URL")


class Config:
    load_dotenv()
    DATABASE_URI = str(DATABASE_URL)


print(Config.DATABASE_URI)
