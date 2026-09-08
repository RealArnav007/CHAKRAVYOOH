import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.database.session import Base
from src.dependencies import get_db_session
from src.config import get_settings
import nacl.public
import nacl.encoding
import nacl.signing

# Set environment to testing
settings = get_settings()
settings.ENVIRONMENT = "testing"
settings.MOCK_OTP = True

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

@pytest_asyncio.fixture(scope="function")
async def async_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def async_client(async_db: AsyncSession):
    async def override_get_db():
        yield async_db

    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def crypto_keys():
    """Generates standard keys for testing."""
    # Backend keys (X25519)
    backend_priv = nacl.public.PrivateKey.generate()
    backend_pub = backend_priv.public_key
    
    # Device keys (Ed25519)
    device_sign = nacl.signing.SigningKey.generate()
    device_verify = device_sign.verify_key
    
    return {
        "backend_priv": backend_priv.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8'),
        "backend_pub": backend_pub.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8'),
        "backend_priv_obj": backend_priv,
        "device_sign": device_sign.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8'),
        "device_verify": device_verify.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8'),
        "device_sign_obj": device_sign,
        "device_verify_obj": device_verify,
    }
