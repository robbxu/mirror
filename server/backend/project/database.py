from typing import Optional
from contextlib import asynccontextmanager, contextmanager
from fastapi import FastAPI, Depends
from celery.signals import worker_process_init, worker_process_shutdown

from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs, create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine as Database

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy.engine import Engine as SyncDB

from project.config import settings

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# https://github.com/tiangolo/fastapi/issues/726
_db_conn: Optional[Database]
_sync_conn: Optional[SyncDB]


# Running migrations: alembic revision --autogenerate
# Double-check the autogenerated code in alembic/versions (see bottom for notes)
# Then run alembic upgrade head

# For usage with FastAPI - don't use contextmanager decorators, as it will mess with Depends
# use Depends instead of with, but only inside FastAPI. 
async def manage_conn_pools(app: FastAPI):
    global _db_conn
    try:
        _db_conn = create_async_engine(
            settings.DATABASE_URL, 
            connect_args=settings.ASYNC_DATABASE_CONNECT_DICT
        ) 
        yield  
        await _db_conn.dispose()
    except Exception as e:
        logger.exception("Error in manage_conn_pools")
        raise


async def get_db_conn() -> Database:
    assert _db_conn is not None
    return _db_conn


async def get_db_sess():
    conn = await get_db_conn()
    #https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession
    sess = AsyncSession(bind=conn, expire_on_commit=False)

    try:
        yield sess
    finally:
        await sess.close()

# SYNC DB CONNECTIONS FOR USE IN CELERY WORKERS --------------------------------------------------------

def open_sync_db_pool():
    global _sync_conn
    # https://stackoverflow.com/questions/73613457/runtimeerror-task-running-at-at-got-future-future-pending-cb-protocol
    _sync_conn = create_engine(
        settings.SYNC_DB_URL, connect_args=settings.SYNC_DATABASE_CONNECT_DICT
    ) # add echo to params above for debugging output


def close_sync_db_pool():
    global _sync_conn
    if _sync_conn:
        _sync_conn.dispose()


def get_sync_conn() -> Database:
    # logger.debug(f"Sync connection state: {globals().get('_sync_conn')}")
    assert _sync_conn is not None
    return _sync_conn


@contextmanager
def get_sync_sess():
    # logger.debug("Entering get_sync_sess")
    # logger.debug(f"Sync connection state: {globals().get('_sync_conn')}")
    
    conn = get_sync_conn()
    sess = Session(bind=conn)

    try:
        # logger.debug("Yielding session")
        yield sess
    except Exception as e:
        logger.exception("Error during session use")
        sess.rollback()
        raise
    finally:
        # logger.debug("Closing session")
        sess.close()

# https://stackoverflow.com/questions/25352437/sqlalchemy-python-using-an-engine-per-process-and-injecting-that-engine-into-d
@worker_process_init.connect
def init_worker(**kwargs):
    open_sync_db_pool()

# https://docs.celeryq.dev/en/stable/userguide/signals.html#worker-process-init
@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    close_sync_db_pool()


# Old Async celery drivers------------------------------------------------------------------------------

# async def open_db_conn_pool():
#     global _db_conn
#     https://stackoverflow.com/questions/73613457/runtimeerror-task-running-at-at-got-future-future-pending-cb-protocol
#     _db_conn = create_async_engine(
#         settings.DATABASE_URL, connect_args=settings.DATABASE_CONNECT_DICT, poolclass=NullPool
#     )


# async def close_db_conn_pool():
#     global _db_conn
#     if _db_conn:
#         await _db_conn.dispose()

# https://stackoverflow.com/questions/42854936/can-i-mount-same-volume-to-multiple-docker-containers
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Changes to make to alembic autogenerated files