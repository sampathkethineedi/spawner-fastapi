from pydantic import BaseSettings
import os


class Settings(BaseSettings):

    DEV = os.getenv("DEV_STATE", True)
    REDIS_URI: str = "ec2-3-83-102-84.compute-1.amazonaws.com"
    REDIS_PASSWORD: str = 'cvision2020'
    S3_URI: str = 'https://cvision.s3.amazonaws.com/'
    SAVE_PATH: str = "camera_events/stable"

    PORT: int = 6060
    IMAGE_NAME: str = "person-counter:2.0"

    API_KEY: str = "cvision2020"

    REDIS_URI_DEV: str = "localhost"
    SAVE_PATH_DEV: str = "camera_events/dev"
