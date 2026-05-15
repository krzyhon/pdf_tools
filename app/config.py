import os

TEMP_BUCKET: str = os.environ["TEMP_BUCKET"]
AWS_REGION: str = os.getenv("AWS_REGION", "eu-west-1")
MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "100"))
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
