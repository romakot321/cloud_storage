import asyncio

import asyncpg
from loguru import logger
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = '127.0.0.1'
    postgres_db: str = 'db'
    postgres_password: str = 'password'
    postgres_user: str = 'postgres'


settings = Settings()


async def connect_create_if_not_exists(user, database, password, host):
    for i in range(5):
        try:
            conn = await asyncpg.connect(
                user=user, database=database,
                password=password, host=host
            )
            await conn.close()
            break
        except asyncpg.InvalidCatalogNameError:
            # Database does not exist, create it.
            sys_conn = await asyncpg.connect(
                database='template1',
                user='postgres',
                password=password,
                host=host
            )
            await sys_conn.execute(
                f'CREATE DATABASE "{database}" OWNER "{user}"'
            )
            await sys_conn.close()
            break
        except Exception as e:
            print(e)
            print('Retry in 5 seconds...')
            await asyncio.sleep(5)


def run_init_db():
    asyncio.run(
        connect_create_if_not_exists(
            settings.postgres_user,
            settings.postgres_db,
            settings.postgres_password,
            settings.postgres_host
        )
    )
    logger.info('DB initialization is done')
