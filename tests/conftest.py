import json
import os

import pytest
from aiopg.sa import create_engine, Engine

from tests import pg_setup
from tests.stubs.users.adapter import UserHTTPAdapter
from tests.stubs.users.repo import PostgresUserRepo, USER


@pytest.fixture
def user_http_adapter():
    return UserHTTPAdapter()


@pytest.fixture
def user_post():
    return json.load(open("./tests/stubs/users/json/POST.json"))


@pytest.fixture
async def engine() -> Engine:
    conf = {
        "host": os.getenv("POSTGRES_HOST", default="127.0.0.1"),
        "port": os.getenv("POSTGRES_PORT", default=5432),
        "user": os.getenv("POSTGRES_USER", default="postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", default="postgres"),
        "database": "aiokea_test",
    }
    return await create_engine(**conf)


@pytest.fixture
async def psql_user_repo(engine):
    pg = PostgresUserRepo(engine)
    yield pg
    pg.engine.close()
    await pg.engine.wait_closed()


@pytest.fixture
async def psql_db(loop, engine, psql_user_repo):

    tables = [USER]

    for table in tables:
        async with engine.acquire() as conn:
            await conn.execute("TRUNCATE TABLE {0} CASCADE".format(table.name))

    await pg_setup.setup_db(psql_user_repo)
    yield

    for table in tables:
        async with engine.acquire() as conn:
            await conn.execute("TRUNCATE TABLE {0} CASCADE".format(table.name))

    engine.close()
    await engine.wait_closed()
