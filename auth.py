import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

import config

api_key_header = APIKeyHeader(name="X-API-Key")


def require_api_key(api_key: str = Security(api_key_header)) -> None:
    if not config.API_KEY or not secrets.compare_digest(api_key, config.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
