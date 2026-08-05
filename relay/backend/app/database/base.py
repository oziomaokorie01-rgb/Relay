from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all Relay SQLAlchemy database models.

    Every ORM model will inherit from this class so SQLAlchemy and Alembic
    can discover the application's database tables.
    """

    pass