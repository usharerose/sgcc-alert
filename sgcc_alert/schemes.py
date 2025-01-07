"""
Object type-hint definition
"""
import datetime
from typing import Optional, TypedDict


class Resident(TypedDict):

    resident_id: int
    is_main: bool
    resident_address: Optional[str]
    developer_name: str


class Usage(TypedDict):

    resident_id: int
    date: datetime.date           # start date of the period
    granularity: str              # date granularity
    elec_usage: Optional[float]   # unit is kilowatt-hour
    elec_charge: Optional[float]  # unit is CNY


class Balance(TypedDict):

    resident_id: int
    date: datetime.date     # start date of the period
    granularity: str        # date granularity
    balance: float          # unit is CNY
    est_remain_days: float  # unit is day
