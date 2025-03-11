from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from project.database import Base
import pytest
import asyncio


@pytest.fixture(scope="function")
async def async_engine():
    return create_async_engine("postgresql+asyncpg://admin:secretkey@db-test/test")


@pytest.fixture(scope="function")
async def async_tables(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def async_session(async_engine, async_tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = await async_engine.connect()
    # begin the nested transaction
    transaction = await connection.begin()
    # use the connection with the already started transaction
    session = AsyncSession(bind=connection)

    yield session

    await session.close()
    # roll back the broader transaction
    await transaction.rollback()
    # put back the connection to the connection pool
    await connection.close()


@pytest.fixture(scope="session")
def sync_engine():
    return create_engine("postgresql://admin:secretkey@db-test/test")


@pytest.fixture(scope="session")
def sync_tables(sync_engine):
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)

@pytest.fixture()
def sync_session(sync_engine, sync_tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = sync_engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()
