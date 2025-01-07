"""
Database schemes used by SQLAlchemy, which store data
"""
import datetime

from sqlalchemy import Boolean, Date, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):

    __abstract__ = True

    created_time: Mapped[int] = mapped_column(
        Integer, nullable=False,
        doc='Unix timestamp when record was created',
        comment='Unix timestamp when record was created'
    )
    updated_time: Mapped[int] = mapped_column(
        Integer, nullable=False,
        doc='Unix timestamp when record was updated',
        comment='Unix timestamp when record was updated'
    )


class DimResident(BaseModel):

    __tablename__ = 'dim_resident'

    resident_id: Mapped[int] = mapped_column(
        Integer, primary_key=True,
        doc='Identifier of resident',
        comment='Identifier of resident'
    )
    is_main: Mapped[bool] = mapped_column(
        Boolean, default=False,
        doc='Whether the resident is main door or not',
        comment='Whether the resident is main door or not'
    )
    resident_address: Mapped[str] = mapped_column(
        String, nullable=True,
        doc='Address of the resident',
        comment='Address of the resident'
    )
    developer_name: Mapped[str] = mapped_column(
        String, nullable=True,
        doc='Developer name of the resident',
        comment='Developer name of the resident'
    )


class FactBalance(BaseModel):

    __tablename__ = 'fact_balance'

    resident_id: Mapped[int] = mapped_column(
        Integer, primary_key=True,
        doc='Identifier of resident',
        comment='Identifier of resident'
    )
    date: Mapped[datetime.date] = mapped_column(
        Date, primary_key=True,
        doc='Ordinal date',
        comment='Ordinal date'
    )
    granularity: Mapped[str] = mapped_column(
        String, primary_key=True,
        doc='Date granularity',
        comment='Date granularity'
    )
    balance: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc='Resident balance',
        comment='Resident balance'
    )
    est_remain_days: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc='Estimate remain days of electricity availability',
        comment='Estimate remain days of electricity availability'
    )


class FactUsage(BaseModel):

    __tablename__ = 'fact_usage'

    resident_id: Mapped[int] = mapped_column(
        Integer, primary_key=True,
        doc='Identifier of resident',
        comment='Identifier of resident'
    )
    date: Mapped[datetime.date] = mapped_column(
        Date, primary_key=True,
        doc='Ordinal date',
        comment='Ordinal date'
    )
    granularity: Mapped[str] = mapped_column(
        String, primary_key=True,
        doc='Date granularity',
        comment='Date granularity'
    )
    elec_usage: Mapped[float] = mapped_column(
        Float, nullable=True,
        doc='Incremental usage of electricity',
        comment='Incremental usage of electricity'
    )
    elec_charge: Mapped[float] = mapped_column(
        Float, nullable=True,
        doc='Incremental electricity charge',
        comment='Incremental electricity charge'
    )
