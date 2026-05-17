from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.models.domain import Principal, Role
from app.security.permissions import max_clearance_for_roles

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


DEMO_USERS = {
    "admin": {"password": "admin-change-me", "roles": [Role.admin], "departments": ["global", "finance", "engineering", "compliance", "operations", "hr"]},
    "fin_user": {"password": "finance-change-me", "roles": [Role.finance], "departments": ["finance"]},
    "eng_user": {"password": "engineering-change-me", "roles": [Role.engineering], "departments": ["engineering"]},
    "comp_user": {"password": "compliance-change-me", "roles": [Role.compliance], "departments": ["compliance", "finance", "operations"]},
    "guest": {"password": "guest-change-me", "roles": [Role.guest], "departments": ["global"]},
}


def authenticate_user(username: str, password: str) -> Principal | None:
    record = DEMO_USERS.get(username)
    if not record or record["password"] != password:
        return None
    roles = record["roles"]
    return Principal(
        user_id=username,
        username=username,
        roles=roles,
        departments=record["departments"],
        clearance=max_clearance_for_roles(roles),
    )


def create_access_token(principal: Principal) -> str:
    settings = get_settings()
    expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = principal.model_dump(mode="json") | {"sub": principal.user_id, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_principal(token: Annotated[str, Depends(oauth2_scheme)]) -> Principal:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return Principal(**{k: payload[k] for k in ["user_id", "username", "roles", "departments", "clearance"]})
    except (JWTError, KeyError, ValueError) as exc:
        raise credentials_exception from exc

