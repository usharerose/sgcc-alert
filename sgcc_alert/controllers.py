"""
Controllers related to request handling
"""
import datetime
from typing import Dict

from flask import render_template, request

from .core.services.query_service import QueryService


def dashboard() -> str:
    return render_template('dashboard.html')


def get_residents() -> Dict:
    order_by = request.args.get('order_by')
    order = request.args.get('order')
    offset_arg = request.args.get('offset')
    offset = None
    if offset_arg is not None:
        offset = int(offset_arg)
    limit_arg = request.args.get('limit')
    limit = None
    if limit_arg is not None:
        limit = int(limit_arg)

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


def get_resident_balances(resident_id: int) -> Dict:
    start_date_arg = request.args.get('start_date')
    start_date = None
    if start_date_arg is not None:
        start_date = datetime.datetime.strptime(
            start_date_arg,
            '%Y-%m-%d'
        ).date()
    end_date_arg = request.args.get('end_date')
    end_date = None
    if end_date_arg is not None:
        end_date = datetime.datetime.strptime(
            end_date_arg,
            '%Y-%m-%d'
        ).date()
    order_by = request.args.get('order_by')
    order = request.args.get('order')
    offset_arg = request.args.get('offset')
    offset = None
    if offset_arg is not None:
        offset = int(offset_arg)
    limit_arg = request.args.get('limit')
    limit = None
    if limit_arg is not None:
        limit = int(limit_arg)

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


def get_resident_usages(resident_id: int) -> Dict:
    granularity = request.args.get('granularity', 'monthly')

    start_date_arg = request.args.get('start_date')
    start_date = None
    if start_date_arg is not None:
        start_date = datetime.datetime.strptime(
            start_date_arg,
            '%Y-%m-%d'
        ).date()
    end_date_arg = request.args.get('end_date')
    end_date = None
    if end_date_arg is not None:
        end_date = datetime.datetime.strptime(
            end_date_arg,
            '%Y-%m-%d'
        ).date()

    order_by = request.args.get('order_by')
    order = request.args.get('order')
    offset_arg = request.args.get('offset')
    offset = None
    if offset_arg is not None:
        offset = int(offset_arg)
    limit_arg = request.args.get('limit')
    limit = None
    if limit_arg is not None:
        limit = int(limit_arg)

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
