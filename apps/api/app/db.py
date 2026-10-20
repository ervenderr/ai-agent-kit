import asyncio
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.models import Note, User

SessionFactory = async_sessionmaker[AsyncSession]


def make_session_factory(settings: Settings | None = None) -> SessionFactory:
    engine = create_async_engine((settings or get_settings()).database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def seed_dev_user() -> None:
    """`python -m app.db`: create a dev user and print its token (the token is the only login)."""
    token = secrets.token_urlsafe(24)
    async with make_session_factory()() as s:
        user = await s.scalar(select(User).where(User.email == "dev@example.com"))
        if user:  # re-running rotates the token
            user.api_token = token
        else:
            user = User(email="dev@example.com", api_token=token, scopes=["notes:read", "calc"])
            s.add(user)
            await s.flush()
            s.add(Note(user_id=user.id, title="Groceries", body="Milk, eggs, bread."))
        await s.commit()
    print(f"dev token: {token}")


if __name__ == "__main__":
    asyncio.run(seed_dev_user())
