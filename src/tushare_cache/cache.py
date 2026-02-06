# -*- coding: utf-8 -*-
"""
===================================
Tushare 缓存服务
===================================

职责：
1. 本地有数据且覆盖到「最新交易日」则直接返回（减少对外部 API 依赖）
2. 缺数据时用 Tushare API 拉取并写入缓存
3. 缺数据情形：股票无数据、数据不是最新、需排除非交易日（依赖交易日历）
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

import pandas as pd

from .trading_calendar import get_trading_calendar, get_latest_trading_day
from .store import TushareCacheStore
from data_provider.base import DataFetchError

logger = logging.getLogger(__name__)


class TushareCacheService:
    """
    Tushare 独立缓存服务。
    - 有缓存且数据覆盖到最新交易日：从本地返回
    - 无缓存或数据不是最新：用 Tushare API 拉取，合并写入缓存后返回
    - 依赖交易日历排除非交易日
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        tushare_token: Optional[str] = None,
    ):
        """
        Args:
            cache_dir: 缓存根目录，默认从环境变量 TUSHARE_CACHE_DIR 或 ./tushare_cache
            tushare_token: Tushare Token，缺省时从配置/环境变量读取
        """
        if cache_dir:
            import os
            os.environ["TUSHARE_CACHE_DIR"] = cache_dir
        self._store = TushareCacheStore()
        self._token = tushare_token
        self._calendar = get_trading_calendar()
        # 本进程内 Tushare API 拉取统计（每次调用 API 时累加）
        self._api_fetch_calls: int = 0
        self._api_fetch_rows: int = 0
        self._api_fetch_codes: List[str] = []

    def _get_token(self) -> Optional[str]:
        if self._token:
            return self._token
        try:
            from src.config import get_config
            return get_config().tushare_token
        except Exception:
            return None

    def _ensure_calendar_from_tushare(self) -> None:
        """若本地无交易日历缓存且配置了 Token，尝试从 Tushare 拉取并保存。"""
        if self._calendar._loaded and not self._calendar._use_fallback_only:
            return
        token = self._get_token()
        if not token:
            return
        # 尝试拉取未来几年
        from datetime import date as d
        end = d.today().year + 2
        self._calendar.fetch_and_save_from_tushare(
            token,
            start_date="20200101",
            end_date=f"{end}1231",
            exchange="SSE",
        )
        self._calendar._loaded = False
        self._calendar._ensure_loaded()

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 90,
    ) -> Tuple[pd.DataFrame, bool]:
        """
        获取日线数据：优先本地缓存，缺数据或非最新时从 Tushare 拉取并写入缓存。

        Args:
            stock_code: 股票代码
            start_date: 开始日期 YYYY-MM-DD（可选）
            end_date: 结束日期 YYYY-MM-DD（可选，默认到「最新交易日」）
            days: 未指定 start_date 时，按最近 days 个交易日估算开始日期

        Returns:
            (DataFrame, from_cache)
            - from_cache=True：本次完全来自本地缓存
            - from_cache=False：本次有从 Tushare API 拉取并已写入缓存

        缺数据情形：
        1. 该股票代码无数据：API 返回空，不写缓存，返回空 DataFrame
        2. 有数据但不是最新：缓存 max_date < 最新交易日，会拉取缺失区间并合并
        3. 非交易日：end_date 会解析为「最新交易日」，不会把周末/节假日当「最新」
        """
        self._ensure_calendar_from_tushare()
        latest_trading = get_latest_trading_day()
        latest_str = latest_trading.strftime("%Y-%m-%d")

        if end_date is None:
            end_date = latest_str
        if start_date is None:
            # 按「最近 days 个交易日」估算开始日（多取一些日历日）
            start_dt = latest_trading - timedelta(days=days * 2)
            start_date = start_dt.strftime("%Y-%m-%d")

        # 1) 尝试从缓存命中
        cached = self._store.read(stock_code)
        if cached is not None and not cached.empty:
            max_cached = cached["date"].max()
            if pd.notna(max_cached):
                max_date = max_cached.date() if hasattr(max_cached, "date") else max_cached
                if max_date >= latest_trading:
                    # 缓存已覆盖到最新交易日，按区间切片返回
                    cached["date"] = pd.to_datetime(cached["date"])
                    mask = (cached["date"] >= start_date) & (cached["date"] <= end_date)
                    out = cached.loc[mask].copy()
                    out = out.sort_values("date", ascending=True).reset_index(drop=True)
                    if not out.empty:
                        logger.info("[TushareCache] 命中缓存 %s: %s ~ %s", stock_code, start_date, end_date)
                        return out, True

        # 2) 缓存未命中或不是最新，从 Tushare 拉取
        token = self._get_token()
        if not token:
            logger.warning("[TushareCache] 未配置 TUSHARE_TOKEN，无法拉取缺失数据")
            if cached is not None and not cached.empty:
                cached["date"] = pd.to_datetime(cached["date"])
                mask = (cached["date"] >= start_date) & (cached["date"] <= end_date)
                out = cached.loc[mask].copy()
                out = out.sort_values("date", ascending=True).reset_index(drop=True)
                return out, True
            raise DataFetchError("Tushare 缓存未命中且未配置 TUSHARE_TOKEN")

        try:
            from data_provider.tushare_fetcher import TushareFetcher
            fetcher = TushareFetcher()
            if not fetcher.is_available():
                raise DataFetchError("Tushare API 不可用")
            raw = fetcher._fetch_raw_data(stock_code, start_date, end_date)
            if raw is None or raw.empty:
                logger.warning("[TushareCache] 该股票无数据: %s", stock_code)
                if cached is not None and not cached.empty:
                    cached["date"] = pd.to_datetime(cached["date"])
                    mask = (cached["date"] >= start_date) & (cached["date"] <= end_date)
                    out = cached.loc[mask].copy()
                    return out.sort_values("date", ascending=True).reset_index(drop=True), True
                return pd.DataFrame(), False
            df = fetcher._normalize_data(raw, stock_code)
            df = fetcher._clean_data(df)
            df = fetcher._calculate_indicators(df)
            self._store.merge_and_write(stock_code, df)
            # 统计本进程 API 拉取量
            rows = len(raw)
            self._api_fetch_calls += 1
            self._api_fetch_rows += rows
            self._api_fetch_codes.append(stock_code)
            df["date"] = pd.to_datetime(df["date"])
            mask = (df["date"] >= start_date) & (df["date"] <= end_date)
            out = df.loc[mask].copy().sort_values("date", ascending=True).reset_index(drop=True)
            logger.info(
                "[TushareCache] 已从 API 拉取并写入缓存: %s，本次拉取 %d 条；累计本进程 API 调用 %d 次、共 %d 条",
                stock_code, rows, self._api_fetch_calls, self._api_fetch_rows,
            )
            return out, False
        except Exception as e:
            logger.warning("[TushareCache] 拉取失败 %s: %s", stock_code, e)
            if cached is not None and not cached.empty:
                cached["date"] = pd.to_datetime(cached["date"])
                mask = (cached["date"] >= start_date) & (cached["date"] <= end_date)
                out = cached.loc[mask].copy()
                out = out.sort_values("date", ascending=True).reset_index(drop=True)
                return out, True
            raise DataFetchError(f"Tushare 缓存拉取失败: {e}") from e

    def get_fetch_stats(self) -> Dict[str, Any]:
        """
        返回本进程内 Tushare API 拉取统计（自服务创建或上次重置以来的累计）。

        Returns:
            dict: {
                "api_calls": int,   # API 调用次数（每只股票一次 daily 算一次）
                "api_rows": int,    # 从 API 拉取的总行数
                "api_codes": list[str],  # 触发过 API 拉取的股票代码列表
            }
        """
        return {
            "api_calls": self._api_fetch_calls,
            "api_rows": self._api_fetch_rows,
            "api_codes": list(self._api_fetch_codes),
        }

    def reset_fetch_stats(self) -> None:
        """重置 API 拉取统计（便于新一轮运行前清零）。"""
        self._api_fetch_calls = 0
        self._api_fetch_rows = 0
        self._api_fetch_codes = []
