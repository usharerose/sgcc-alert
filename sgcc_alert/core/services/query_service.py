"""
Query service
"""
from typing import Dict, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query, scoped_session

from ...constants import DateGranularity
from ...databases.models import DimResident, FactBalance
from ...databases.session import managed_session


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


def get_order_func(order: str):
    if order == 'asc':
        return asc
    if order == 'desc':
        return desc
    raise ValueError(f'{order} is unavailable sort')
