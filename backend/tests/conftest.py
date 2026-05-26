import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base
from app.core.deps import get_db
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
