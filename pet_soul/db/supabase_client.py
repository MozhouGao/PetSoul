"""
Supabase client — replaces SQLAlchemy + SQLite.

Provides a shared Supabase client instance and table helpers.

Required Supabase tables (create via Supabase Dashboard → SQL Editor):

    CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,       -- Auth0 sub (e.g. "auth0|abc123")
        email       TEXT,
        name        TEXT,
        created_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS pets (
        id              BIGSERIAL PRIMARY KEY,
        user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        species         TEXT DEFAULT 'dog',
        breed           TEXT DEFAULT '',
        breed_confidence FLOAT DEFAULT 0.0,
        profile_json    JSONB DEFAULT '{}',
        texture_prompt  TEXT DEFAULT '',
        model_filename  TEXT DEFAULT '',
        created_at      TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_pets_user_id ON pets(user_id);

    CREATE TABLE IF NOT EXISTS motion_data (
        id          BIGSERIAL PRIMARY KEY,
        pet_id      BIGINT NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        keypoints   JSONB NOT NULL,         -- T x J x 3 serialised
        stats       JSONB DEFAULT '{}',     -- motion statistics
        created_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS personality_profiles (
        id          BIGSERIAL PRIMARY KEY,
        pet_id      BIGINT NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        vector      JSONB NOT NULL,         -- personality embedding
        created_at  TIMESTAMPTZ DEFAULT now()
    );
"""

import logging
from typing import Optional

from supabase import create_client, Client

from pet_soul.config import CONFIG

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_supabase() -> Client:
    """Return the shared Supabase client, creating it on first call."""
    global _client
    if _client is None:
        if not CONFIG.supabase_url or not CONFIG.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(CONFIG.supabase_url, CONFIG.supabase_key)
        logger.info("Supabase client initialised for %s", CONFIG.supabase_url)
    return _client


def is_supabase_ready() -> bool:
    """Check whether Supabase credentials are configured."""
    return bool(CONFIG.supabase_url and CONFIG.supabase_key)
