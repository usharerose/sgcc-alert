"""
Query service
"""
import datetime
from typing import cast, Dict, List, Optional, TypedDict

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query, scoped_session

from ...constants import DateGranularity
from ...databases.models import DimResident, FactBalance, FactUsage
from ...databases.session import managed_session


class Resident(TypedDict):

    resident_id: int
    is_main: bool
    resident_address: str
    developer_name: str


class ResidentBalance(TypedDict):

    resident_id: int
    date: int
    granularity: str
    balance: float
    est_remain_days: float


class ResidentUsage(TypedDict):

    resident_id: int
    date: int
    granularity: str
    elec_usage: float
    elec_charge: float


class QueryService:

    @classmethod
    def query_resident(
        cls,
        resident_id: Optional[List[int]] = None,
        exclude_non_main_resident: Optional[bool] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        pagination: Optional[Dict[str, int]] = None
    ):
        with managed_session() as session:
            result = cls._query_resident(session, resident_id, exclude_non_main_resident, order_by, pagination)
        return result

    @classmethod
    def _query_resident(
        cls,
        session: scoped_session,
        resident_id: Optional[List[int]] = None,
        exclude_non_main_resident: Optional[bool] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        pagination: Optional[Dict[str, int]] = None
    ):
        query: Query = session.query(
            DimResident.resident_id,
            DimResident.is_main,
            DimResident.resident_address,
            DimResident.developer_name
        )
        if resident_id is not None:
            query = query.filter(DimResident.resident_id.in_(resident_id))
        if exclude_non_main_resident is not None:
            query = query.filter(DimResident.is_main.is_(exclude_non_main_resident))
        if order_by is not None:
            order_args = []
            for order_item in order_by:
                order_func = get_order_func(order_item['order'])
                order_args.append(order_func(getattr(DimResident, order_item['item'])))
            query = query.order_by(*order_args)
        if pagination is not None:
            query = query.limit(pagination['limit']).offset(pagination['offset'])

        columns = [column['name'] for column in query.column_descriptions]
        result = [dict(zip(columns, item)) for item in query.all()]
        return result

    @classmethod
    def query_latest_balance(
        cls,
        resident_id: int
    ):
        with managed_session() as session:
            result = cls._query_latest_balance(session, resident_id)
        return result

    @classmethod
    def _query_latest_balance(
        cls,
        session: scoped_session,
        resident_id: int
    ):
        query: Query = session.query(
            FactBalance.resident_id,
            FactBalance.date,
            FactBalance.balance,
            FactBalance.est_remain_days,
        ).filter(
            FactBalance.resident_id.in_([resident_id]),
            FactBalance.granularity.in_([DateGranularity.DAILY.value])
        ).order_by(
            desc(FactBalance.date)
        ).limit(1)

        columns = [column['name'] for column in query.column_descriptions]
        result = [dict(zip(columns, item)) for item in query.all()]
        return result

    @classmethod
    def query_residents(
        cls,
        order_by: Optional[str] = 'resident_id',
        order: Optional[str] = 'asc',
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Resident]:
        with managed_session() as session:
            result = cls._query_residents(
                session,
                order_by,
                order,
                offset,
                limit
            )
        return result

    @classmethod
    def _query_residents(
        cls,
        session: scoped_session,
        order_by: Optional[str] = 'resident_id',
        order: Optional[str] = 'asc',
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Resident]:
        if order_by is None:
            order_by = 'resident_id'
        if order is None:
            order = 'asc'

        query: Query = session.query(
            DimResident.resident_id,
            DimResident.is_main,
            DimResident.resident_address,
            DimResident.developer_name
        )

        order_func = get_order_func(order)
        query = query.order_by(order_func(getattr(DimResident, order_by)))

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        columns = [column['name'] for column in query.column_descriptions]
        result = cast(
            List[Resident],
            [dict(zip(columns, item)) for item in query.all()]
        )
        return result

    @classmethod
    def query_resident_balances(
        cls,
        resident_id: int,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        order_by: Optional[str] = 'date',
        order: Optional[str] = 'asc',
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ResidentBalance]:
        with managed_session() as session:
            result = cls._query_resident_balances(
                session,
                resident_id,
                start_date,
                end_date,
                order_by,
                order,
                offset,
                limit
            )
        return result

    @classmethod
    def _query_resident_balances(
        cls,
        session: scoped_session,
        resident_id: int,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        order_by: Optional[str] = 'date',
        order: Optional[str] = 'asc',
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ResidentBalance]:
        if order_by is None:
            order_by = 'date'
        if order is None:
            order = 'asc'

        query: Query = session.query(
            FactBalance.resident_id,
            FactBalance.date,
            FactBalance.granularity,
            FactBalance.balance,
            FactBalance.est_remain_days,
        ).filter(
            FactBalance.resident_id == resident_id,
            FactBalance.granularity == DateGranularity.DAILY.value
        )
        if start_date is not None:
            query = query.filter(FactBalance.date >= start_date.toordinal())
        if end_date is not None:
            query = query.filter(FactBalance.date <= end_date.toordinal())

        order_func = get_order_func(order)
        query = query.order_by(order_func(getattr(FactBalance, order_by)))

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        columns = [column['name'] for column in query.column_descriptions]
        result = cast(
            List[ResidentBalance],
            [dict(zip(columns, item)) for item in query.all()]
        )
        return result

    @classmethod
    def query_resident_usages(
        cls,
        resident_id: int,
        granularity: str,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        order_by: Optional[str] = 'date',
        order: Optional[str] = 'asc',
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ResidentUsage]:
        with managed_session() as session:
            result = cls._query_resident_usages(
                session,
                resident_id,
                granularity,
                start_date,
                end_date,
                order_by,
                order,
                offset,
                limit
            )
        return result

    @classmethod
    def _query_resident_usages(
        cls,
        session: scoped_session,
        resident_id: int,
        granularity: str,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        order_by: Optional[str] = 'date',
        order: Optional[str] = 'asc',
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ResidentUsage]:
        if order_by is None:
            order_by = 'date'
        if order is None:
            order = 'asc'

        query: Query = session.query(
            FactUsage.resident_id,
            FactUsage.date,
            FactUsage.granularity,
            FactUsage.elec_usage,
            FactUsage.elec_charge
        ).filter(
            FactUsage.resident_id == resident_id,
            FactUsage.granularity == granularity
        )
        if start_date is not None:
            query = query.filter(FactUsage.date >= start_date.toordinal())
        if end_date is not None:
            query = query.filter(FactUsage.date <= end_date.toordinal())

        order_func = get_order_func(order)
        query = query.order_by(order_func(getattr(FactUsage, order_by)))

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        columns = [column['name'] for column in query.column_descriptions]
        result = cast(
            List[ResidentUsage],
            [dict(zip(columns, item)) for item in query.all()]
        )
        return result


def get_order_func(order: str):
    if order == 'asc':
        return asc
    if order == 'desc':
        return desc
    raise ValueError(f'{order} is unavailable sort')
