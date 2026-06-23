import base64
import hashlib
import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _sign(value: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return digest


def create_token(email: str, settings: Settings) -> str:
    """Create a stateless, signed token: base64(email).hmac(email)."""
    encoded = base64.urlsafe_b64encode(email.encode()).decode().rstrip("=")
    signature = _sign(email, settings.secret_key)
    return f"{encoded}.{signature}"


def verify_token(token: str, settings: Settings) -> str | None:
    try:
        encoded, signature = token.split(".", 1)
        padding = "=" * (-len(encoded) % 4)
        email = base64.urlsafe_b64decode(encoded + padding).decode()
    except Exception:
        return None

    expected = _sign(email, settings.secret_key)
    if not hmac.compare_digest(signature, expected):
        return None
    return email


def authenticate(email: str, password: str, settings: Settings) -> bool:
    return hmac.compare_digest(email, settings.kb_portal_user) and hmac.compare_digest(
        password, settings.kb_portal_password
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = verify_token(credentials.credentials, settings)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return email
