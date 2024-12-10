"""
Object type-hint definition
"""
from typing import Optional, TypedDict


class Usage(TypedDict):

    date: int                     # ordinal date, start date of the period
    granularity: str              # date granularity
    elec_usage: Optional[float]   # unit is kilowatt-hour
    elec_charge: Optional[float]  # unit is CNY


class Balance(TypedDict):

    date: int               # ordinal date, start date of the period
    granularity: str        # date granularity
    balance: float          # unit is CNY
    est_remain_days: float  # unit is day
