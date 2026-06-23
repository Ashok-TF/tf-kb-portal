from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import authenticate, create_token, current_user
from app.config import Settings, get_settings
from app.schemas import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, settings: Settings = Depends(get_settings)) -> LoginResponse:
    if not authenticate(payload.email, payload.password, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    token = create_token(payload.email, settings)
    return LoginResponse(token=token, email=payload.email)


@router.get("/me", response_model=MeResponse)
def me(email: str = Depends(current_user)) -> MeResponse:
    return MeResponse(email=email)
