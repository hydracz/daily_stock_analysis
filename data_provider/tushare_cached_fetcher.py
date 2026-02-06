# -*- coding: utf-8 -*-
"""
===================================
TushareCachedFetcher - 带本地缓存的 Tushare 数据源
===================================

职责：
1. 优先从本地 Tushare 缓存返回数据（减少对外部 API 依赖）
2. 缺数据或数据不是最新时用 Tushare API 拉取并写入缓存
3. 依赖交易日历排除非交易日，以「最新交易日」判断是否需更新
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from .base import BaseFetcher, DataFetchError
from src.tushare_cache import TushareCacheService

logger = logging.getLogger(__name__)


class TushareCachedFetcher(BaseFetcher):
    """
    带独立缓存的 Tushare 数据源。
    - 本地有数据且覆盖到最新交易日则直接返回
    - 缺数据或非最新时用 Tushare API 拉取并写入缓存
    """

    name = "TushareCachedFetcher"
    priority = -2  # 比 TushareFetcher(-1) 更高，优先用缓存

    def __init__(self):
        self._cache = TushareCacheService()

    def is_available(self) -> bool:
        """有 Tushare Token 或本地已有缓存目录时视为可用。"""
        try:
            from src.config import get_config
            if get_config().tushare_token:
                return True
        except Exception:
            pass
        return self._cache._store._root.exists()

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """仅用于满足基类抽象，实际走 get_daily_data 的缓存逻辑。"""
        raise NotImplementedError("TushareCachedFetcher 请使用 get_daily_data，不走 _fetch_raw_data")

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """仅用于满足基类抽象。"""
        return df

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 90,
    ) -> pd.DataFrame:
        """
        获取日线数据：优先本地缓存，缺数据或非最新时从 Tushare 拉取并写入缓存。
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            from datetime import timedelta
            from src.tushare_cache import get_latest_trading_day
            latest = get_latest_trading_day()
            start_dt = latest - timedelta(days=days * 2)
            start_date = start_dt.strftime("%Y-%m-%d")

        try:
            df, from_cache = self._cache.get_daily_data(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                days=days,
            )
        except DataFetchError:
            raise
        except Exception as e:
            raise DataFetchError(f"Tushare 缓存获取失败: {e}") from e

        if df is None or df.empty:
            raise DataFetchError(f"[{self.name}] 未获取到 {stock_code} 的数据")

        logger.info(
            "[%s] %s 获取成功，共 %d 条，来源: %s",
            self.name,
            stock_code,
            len(df),
            "本地缓存" if from_cache else "Tushare API",
        )
        return df

    def get_fetch_stats(self) -> dict:
        """
        返回本进程内从 Tushare API 拉取的统计（本次运行以来累计）。

        Returns:
            dict: api_calls（API 调用次数）, api_rows（拉取行数）, api_codes（触发 API 的股票代码列表）
        """
        return self._cache.get_fetch_stats()
