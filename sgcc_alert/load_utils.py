"""
Utilities on store data
"""
import datetime
from typing import List

from sqlalchemy import text

from .databases import DimResident, FactBalance, FactUsage, managed_session
from .schemes import Balance, Resident, Usage


SQL_TML_INSERT_RESIDENTS = f'''
    INSERT INTO {DimResident.__tablename__} (
        resident_id,
        is_main,
        resident_address,
        developer_name,
        created_time,
        updated_time
    )
    VALUES (
        :resident_id,
        :is_main,
        :resident_address,
        :developer_name,
        :created_time,
        :updated_time
    )
    ON CONFLICT (
        resident_id
    )
    DO UPDATE
    SET
        is_main = EXCLUDED.is_main,
        resident_address = EXCLUDED.resident_address,
        developer_name = EXCLUDED.developer_name,
        updated_time = EXCLUDED.updated_time
'''


SQL_TML_INSERT_BALANCES = f'''
    INSERT INTO {FactBalance.__tablename__} (
        resident_id,
        date,
        granularity,
        balance,
        est_remain_days,
        created_time,
        updated_time
    )
    VALUES (
        :resident_id,
        :date,
        :granularity,
        :balance,
        :est_remain_days,
        :created_time,
        :updated_time
    )
    ON CONFLICT (
        resident_id,
        date,
        granularity
    )
    DO UPDATE
    SET
        balance = EXCLUDED.balance,
        est_remain_days = EXCLUDED.est_remain_days,
        updated_time = EXCLUDED.updated_time
'''


SQL_TML_INSERT_USAGE = f'''
    INSERT INTO {FactUsage.__tablename__} (
        resident_id,
        date,
        granularity,
        elec_usage,
        elec_charge,
        created_time,
        updated_time
    )
    VALUES (
        :resident_id,
        :date,
        :granularity,
        :elec_usage,
        :elec_charge,
        :created_time,
        :updated_time
    )
    ON CONFLICT (
        resident_id,
        date,
        granularity
    )
    DO UPDATE
    SET
        elec_usage = EXCLUDED.elec_usage,
        elec_charge = EXCLUDED.elec_charge,
        updated_time = EXCLUDED.updated_time
'''


def load_residents(residents: List[Resident]) -> None:
    cur_utc_timestamp = int(datetime.datetime.utcnow().timestamp())
    with managed_session() as session:
        session.execute(
            text(SQL_TML_INSERT_RESIDENTS),
            [
                {
                    'resident_id': resident['resident_id'],
                    'is_main': resident['is_main'],
                    'resident_address': resident['resident_address'],
                    'developer_name': resident['developer_name'],
                    'created_time': cur_utc_timestamp,
                    'updated_time': cur_utc_timestamp
                }
                for resident in residents
            ]
        )


def load_balances(balances: List[Balance]) -> None:
    cur_utc_timestamp = int(datetime.datetime.utcnow().timestamp())
    with managed_session() as session:
        session.execute(
            text(SQL_TML_INSERT_BALANCES),
            [
                {
                    'resident_id': balance['resident_id'],
                    'date': balance['date'],
                    'granularity': balance['granularity'],
                    'balance': balance['balance'],
                    'est_remain_days': balance['est_remain_days'],
                    'created_time': cur_utc_timestamp,
                    'updated_time': cur_utc_timestamp
                }
                for balance in balances
            ]
        )


def load_usages(usages: List[Usage]) -> None:
    cur_utc_timestamp = int(datetime.datetime.utcnow().timestamp())
    with managed_session() as session:
        session.execute(
            text(SQL_TML_INSERT_USAGE),
            [
                {
                    'resident_id': usage['resident_id'],
                    'date': usage['date'],
                    'granularity': usage['granularity'],
                    'elec_usage': usage['elec_usage'],
                    'elec_charge': usage['elec_charge'],
                    'created_time': cur_utc_timestamp,
                    'updated_time': cur_utc_timestamp
                }
                for usage in usages
            ]
        )
