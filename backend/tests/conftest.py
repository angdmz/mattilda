import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.db import Base, get_db
from app.settings import Settings
from app.dependencies import get_cache
from tests.mock_cache import MockCache


@pytest.fixture(scope="session")
def db_test_settings() -> Settings:
    return Settings(db_name="mattilda_test")


@pytest.fixture(scope="session")
def test_engine(db_test_settings: Settings):
    # Ensure test database exists before creating engine
    _ensure_test_database_exists(db_test_settings)
    return create_async_engine(db_test_settings.database_url, echo=False)


def _ensure_test_database_exists(settings: Settings) -> None:
    """Create test database if it doesn't exist."""
    # Connect to postgres database to create test database
    postgres_url = settings.database_url_sync.set(database='postgres')
    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": settings.db_name}
        )
        exists = result.fetchone() is not None
        
        if not exists:
            # CREATE DATABASE cannot run in a transaction block
            conn.execute(text(f'CREATE DATABASE "{settings.db_name}"'))
    
    engine.dispose()


@pytest.fixture(scope="session")
def test_sessionmaker(test_engine):
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session(test_engine, test_sessionmaker) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with test_sessionmaker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def authenticated_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Create a client with authentication token."""
    # Register a test user
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    
    # Login to get token
    login_response = await client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Add authorization header to client
    client.headers["Authorization"] = f"Bearer {token}"
    
    yield client
    
    # Clean up
    if "Authorization" in client.headers:
        del client.headers["Authorization"]


@pytest.fixture(scope="function")
async def mock_cache() -> MockCache:
    """Create a mock cache instance for testing."""
    return MockCache()


@pytest.fixture(scope="function")
async def client_with_mock_cache(db_session: AsyncSession, mock_cache: MockCache) -> AsyncGenerator[tuple[AsyncClient, MockCache], None]:
    """Create a client with mock cache dependency override."""
    async def override_get_db():
        yield db_session
    
    async def override_get_cache():
        return mock_cache
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = override_get_cache
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac, mock_cache
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def authenticated_client_with_mock_cache(client_with_mock_cache: tuple[AsyncClient, MockCache]) -> AsyncGenerator[tuple[AsyncClient, MockCache], None]:
    """Create an authenticated client with mock cache."""
    client, mock_cache = client_with_mock_cache
    
    # Register a test user
    await client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    
    # Login to get token
    login_response = await client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Add authorization header to client
    client.headers["Authorization"] = f"Bearer {token}"
    
    yield client, mock_cache
    
    # Clean up
    if "Authorization" in client.headers:
        del client.headers["Authorization"]
