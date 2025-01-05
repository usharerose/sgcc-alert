"""
Routes of API
"""
import datetime
from typing import Dict

from flask import Blueprint, request

from .core.services.query_service import QueryService


API_V1 = Blueprint('api_v1', __name__)


@API_V1.route('/residents', methods=['GET'])
def get_residents() -> Dict:
    order_by = request.args.get('order_by')
    order = request.args.get('order')
    offset = request.args.get('offset')
    if offset is not None:
        offset = int(offset)
    limit = request.args.get('limit')
    if limit is not None:
        limit = int(limit)

    result = QueryService.query_residents(
        order_by,
        order,
        offset,
        limit
    )

    pagination = None
    if limit is not None:
        _offset = offset if offset else 0
        pagination = {
            'offset': _offset,
            'limit': limit,
            'next_offset': _offset + limit if len(result) == limit else None
        }

    return {
        'data': result,
        'pagination': pagination
    }


@API_V1.route('/residents/<int:resident_id>/balances', methods=['GET'])
def get_resident_balances(resident_id: int) -> Dict:
    start_date = request.args.get('start_date')
    if start_date is not None:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.args.get('end_date')
    if end_date is not None:
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    order_by = request.args.get('order_by')
    order = request.args.get('order')
    offset = request.args.get('offset')
    if offset is not None:
        offset = int(offset)
    limit = request.args.get('limit')
    if limit is not None:
        limit = int(limit)

    result = QueryService.query_resident_balances(
        resident_id,
        start_date,
        end_date,
        order_by,
        order,
        offset,
        limit
    )

    pagination = None
    if limit is not None:
        _offset = offset if offset else 0
        pagination = {
            'offset': _offset,
            'limit': limit,
            'next_offset': _offset + limit if len(result) == limit else None
        }

    return {
        'data': result,
        'pagination': pagination
    }


@API_V1.route('/residents/<int:resident_id>/usages', methods=['GET'])
def get_resident_usages(resident_id: int) -> Dict:
    start_date = request.args.get('start_date')
    granularity = request.args.get('granularity', 'monthly')

    if start_date is not None:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.args.get('end_date')
    if end_date is not None:
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    order_by = request.args.get('order_by')
    order = request.args.get('order')
    offset = request.args.get('offset')
    if offset is not None:
        offset = int(offset)
    limit = request.args.get('limit')
    if limit is not None:
        limit = int(limit)

    result = QueryService.query_resident_usages(
        resident_id,
        granularity,
        start_date,
        end_date,
        order_by,
        order,
        offset,
        limit
    )

    pagination = None
    if limit is not None:
        _offset = offset if offset else 0
        pagination = {
            'offset': _offset,
            'limit': limit,
            'next_offset': _offset + limit if len(result) == limit else None
        }

    return {
        'data': result,
        'pagination': pagination
    }
