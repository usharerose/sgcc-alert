"""
Database session
"""
from contextlib import contextmanager
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import BaseModel
from ..constants import DATABASE_INIT_RETRY_LIMIT


def get_engine():
    return create_engine('sqlite:///app.db')


def get_session():
    engine = get_engine()
    session = scoped_session(
        sessionmaker(bind=engine, autoflush=True, expire_on_commit=True)
    )
    return session


SESSION = get_session()


@contextmanager
def managed_session():
    try:
        yield SESSION
        SESSION.commit()
    except:  # NOQA
        SESSION.rollback()
        raise
    finally:
        SESSION.close()


def prepare_models() -> None:
    retries = 0
    while True:
        try:
            with managed_session() as session:
                BaseModel.metadata.create_all(session.bind)
        except DatabaseError:
            if retries < DATABASE_INIT_RETRY_LIMIT:
                time.sleep(10)
                retries += 1
            else:
                break
        else:
            break
