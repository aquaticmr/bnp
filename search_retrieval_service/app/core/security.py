from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
security_scheme = HTTPBearer(auto_error=False)

def verify_bearer_token(credentials: HTTPAuthorizationCredentials=Security(security_scheme)) -> bool:
    if not settings.REQUIRE_AUTH:
        return True
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing Authorization header', headers={'WWW-Authenticate': 'Bearer'})
    if credentials.credentials != settings.API_BEARER_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid or expired bearer token', headers={'WWW-Authenticate': 'Bearer'})
    return True