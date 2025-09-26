# This file will contain utility functions for the backend.
from typing import Annotated
from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader
import re

SECRET_TOKEN_REGEX = r"^ABC\d{3}$"

async def verify_token(
    token: Annotated[str, Security(APIKeyHeader(name="Authorization", auto_error=False))]
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "API key"},
        )

    # Token must strictly match "ABC" + 3 digits (total length = 6 chars)
    if not re.fullmatch(SECRET_TOKEN_REGEX, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "API key"},
        )

    return token  # return validated token