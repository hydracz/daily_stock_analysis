# -*- coding: utf-8 -*-
"""
===================================
Tushare 独立缓存模块
===================================

职责：
1. 本地优先：有缓存且数据覆盖到最新交易日则直接返回，减少对外部 API 依赖
2. 缺数据时用 Tushare API 拉取并写入缓存
3. 缺数据情形：股票无数据、数据不是最新、需排除非交易日（依赖交易日历）

使用方式：
- 作为库：from src.tushare_cache import TushareCacheService; svc = TushareCacheService(); df, from_cache = svc.get_daily_data('600519', days=90)
- 作为 Fetcher：使用 TushareCachedFetcher（在 data_provider 中），可被 DataFetcherManager 使用
"""

from .trading_calendar import (
    TradingCalendar,
    get_trading_calendar,
    is_trading_day,
    get_latest_trading_day,
)
from .store import TushareCacheStore
from .cache import TushareCacheService

__all__ = [
    "TradingCalendar",
    "get_trading_calendar",
    "is_trading_day",
    "get_latest_trading_day",
    "TushareCacheStore",
    "TushareCacheService",
]
