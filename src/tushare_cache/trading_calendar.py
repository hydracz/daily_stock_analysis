# -*- coding: utf-8 -*-
"""
===================================
A 股交易日历
===================================

职责：
1. 判断某日是否为交易日（排除周末与法定节假日）
2. 获取「某日及之前」的最近一个交易日
3. 优先使用 Tushare trade_cal 拉取并缓存；无 API 时退化为仅排除周末
"""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)

# 缓存文件名（放在缓存根目录下）
CALENDAR_CACHE_FILENAME = ".calendar.csv"

# 常见 A 股休市日（仅作无 API 时的兜底，有 API 时以 trade_cal 为准）
# 格式 YYYY-MM-DD，可按需扩展
FALLBACK_CLOSED_DAYS: Set[str] = set()


def _get_cache_root() -> Path:
    """缓存根目录（与 TushareCacheStore 一致）。"""
    import os
    root = os.getenv("TUSHARE_CACHE_DIR", "./tushare_cache")
    path = Path(root)
    if not path.is_absolute():
        base = Path(__file__).resolve().parent.parent.parent
        path = (base / root).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parse_cal_date(s: str) -> Optional[date]:
    """解析 YYYYMMDD 或 YYYY-MM-DD 为 date。"""
    s = s.strip().replace("-", "")
    if len(s) != 8:
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


class TradingCalendar:
    """
    A 股交易日历。
    - 有缓存文件时：从 .calendar.csv 读取 is_open
    - 无缓存时：退化为仅排除周六、周日
    """

    def __init__(self, cache_root: Optional[Path] = None):
        self._cache_root = cache_root or _get_cache_root()
        self._calendar_path = self._cache_root / CALENDAR_CACHE_FILENAME
        # 内存缓存：date -> is_open (True=交易日)
        self._open_dates: Set[date] = set()
        self._closed_dates: Set[date] = set()
        self._loaded = False
        self._use_fallback_only = False

    def _load_from_file(self) -> bool:
        """从已缓存的 CSV 加载。返回是否加载成功。"""
        if not self._calendar_path.exists():
            return False
        try:
            import csv
            with open(self._calendar_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cal_date = row.get("cal_date") or row.get("date")
                    is_open = row.get("is_open", "1").strip() == "1"
                    d = _parse_cal_date(str(cal_date))
                    if d is not None:
                        if is_open:
                            self._open_dates.add(d)
                        else:
                            self._closed_dates.add(d)
            self._loaded = True
            logger.debug("交易日历已从缓存加载: %s", self._calendar_path)
            return True
        except Exception as e:
            logger.warning("加载交易日历缓存失败 %s: %s", self._calendar_path, e)
            return False

    def _is_weekend(self, d: date) -> bool:
        """周六=5, 周日=6."""
        return d.weekday() >= 5

    def _ensure_loaded(self) -> None:
        if self._loaded or self._use_fallback_only:
            return
        if self._load_from_file():
            return
        self._use_fallback_only = True
        self._loaded = True
        logger.info("交易日历无缓存，使用周末排除模式（周六、周日为非交易日）")

    def is_trading_day(self, d: date) -> bool:
        """
        判断 d 是否为 A 股交易日。
        - 若已加载 trade_cal 缓存：按 is_open 判断
        - 否则：仅排除周六、周日
        """
        self._ensure_loaded()
        if self._use_fallback_only:
            return not self._is_weekend(d)
        if d in self._open_dates:
            return True
        if d in self._closed_dates:
            return False
        # 缓存中未出现的日期：按周末兜底
        return not self._is_weekend(d)

    def get_latest_trading_day(self, before_or_on: Optional[date] = None) -> date:
        """
        获取 before_or_on 及之前的最近一个交易日。
        若 before_or_on 为 None，则使用今天。
        """
        d = before_or_on or date.today()
        self._ensure_loaded()
        while d >= date(1990, 1, 1):
            if self.is_trading_day(d):
                return d
            d -= timedelta(days=1)
        return d

    def fetch_and_save_from_tushare(
        self,
        token: str,
        start_date: str = "20200101",
        end_date: str = "20301231",
        exchange: str = "SSE",
    ) -> bool:
        """
        从 Tushare 拉取交易日历并写入缓存。
        start_date/end_date 格式：YYYYMMDD。
        返回是否成功。
        """
        try:
            import tushare as ts
            api = ts.pro_api(token)
            df = api.trade_cal(
                exchange=exchange,
                start_date=start_date,
                end_date=end_date,
            )
            if df is None or df.empty:
                logger.warning("Tushare trade_cal 返回为空")
                return False
            out = self._cache_root / CALENDAR_CACHE_FILENAME
            df.to_csv(out, index=False, encoding="utf-8-sig")
            logger.info("交易日历已从 Tushare 拉取并保存: %s", out)
            # 清空内存缓存以便下次使用新文件
            self._open_dates.clear()
            self._closed_dates.clear()
            self._loaded = False
            self._use_fallback_only = False
            return True
        except Exception as e:
            logger.warning("从 Tushare 拉取交易日历失败: %s", e)
            return False


# 单例
_calendar: Optional[TradingCalendar] = None


def get_trading_calendar() -> TradingCalendar:
    global _calendar
    if _calendar is None:
        _calendar = TradingCalendar()
    return _calendar


def is_trading_day(d: date) -> bool:
    """判断 d 是否为 A 股交易日。"""
    return get_trading_calendar().is_trading_day(d)


def get_latest_trading_day(before_or_on: Optional[date] = None) -> date:
    """获取 before_or_on 及之前的最近一个交易日。"""
    return get_trading_calendar().get_latest_trading_day(before_or_on)
