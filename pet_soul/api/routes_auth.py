"""
Auth routes — Auth0 integration

The frontend handles Auth0 login via Universal Login or SDK.
These endpoints let the frontend exchange/verify tokens and manage profiles.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from pet_soul.config import CONFIG
from pet_soul.db.auth import get_current_user
from pet_soul.db.supabase_client import get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None


class Auth0ConfigResponse(BaseModel):
    domain: str
    client_id: str
    audience: str


@router.get("/config", response_model=Auth0ConfigResponse)
def auth_config():
    """Return Auth0 config for the frontend to initialise the SDK."""
    return Auth0ConfigResponse(
        domain=CONFIG.auth0_domain,
        client_id=CONFIG.auth0_client_id,
        audience=CONFIG.auth0_audience,
    )


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user profile from the Auth0 token."""
    return UserResponse(
        id=user.get("sub", ""),
        email=user.get("email"),
        name=user.get("name"),
    )


@router.post("/sync")
def sync_user(user: dict = Depends(get_current_user)):
    """Ensure the Auth0 user exists in the Supabase users table.

    Called by the frontend after first login to create the DB record.
    """
    sb = get_supabase()
    user_id = user.get("sub", "")
    email = user.get("email", "")
    name = user.get("name", "")

    # Upsert — insert if new, update if exists
    sb.table("users").upsert(
        {"id": user_id, "email": email, "name": name},
        on_conflict="id",
    ).execute()

    return {"synced": True, "user_id": user_id}
