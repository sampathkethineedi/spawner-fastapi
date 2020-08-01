# IMPORTANT
# rename this file to config.py and add the details

from pydantic import BaseSettings
import os


class Settings(BaseSettings):

    DEV = os.getenv("DEV_STATE", True)
    REDIS_URI: str = ""
    REDIS_PASSWORD: str = ''
    S3_URI: str = ''
    SAVE_PATH: str = "camera_events/stable"

    PORT: int = 6060
    IMAGE_NAME: str = "person-counter:2.0"

    API_KEY: str = ""
