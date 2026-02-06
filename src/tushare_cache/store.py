# -*- coding: utf-8 -*-
"""
===================================
Tushare 缓存存储
===================================

职责：
1. 按股票代码存储日线 CSV：{cache_root}/{code}/daily.csv
2. 列与标准化格式一致：code, date, open, high, low, close, volume, amount, pct_chg（及 ma5, ma10, ma20, volume_ratio 若存在）
3. 支持读取、合并写入（按日期去重，保留最新写入）
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _get_cache_root() -> Path:
    import os
    root = os.getenv("TUSHARE_CACHE_DIR", "./tushare_cache")
    path = Path(root)
    if not path.is_absolute():
        base = Path(__file__).resolve().parent.parent.parent
        path = (base / root).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


class TushareCacheStore:
    """
    按股票代码存储的 Tushare 日线缓存。
    路径：{cache_root}/{stock_code}/daily.csv
    """

    def __init__(self, cache_root: Optional[Path] = None):
        self._root = cache_root or _get_cache_root()

    def _path(self, stock_code: str) -> Path:
        """某只股票的 daily.csv 路径。"""
        code = str(stock_code).strip()
        dir_path = self._root / code
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / "daily.csv"

    def has_cache(self, stock_code: str) -> bool:
        """是否存在该股票的缓存文件且非空。"""
        p = self._path(stock_code)
        if not p.exists():
            return False
        try:
            df = pd.read_csv(p, nrows=1, encoding="utf-8-sig")
            return df is not None and not df.empty
        except Exception:
            return False

    def read(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        读取该股票的全部缓存数据。
        返回 DataFrame 或 None（文件不存在/读失败）。
        保证含 date 列且为日期类型，按 date 升序。
        """
        p = self._path(stock_code)
        if not p.exists():
            return None
        try:
            df = pd.read_csv(p, encoding="utf-8-sig")
            if df is None or df.empty:
                return None
            if "date" not in df.columns:
                logger.warning("缓存缺少 date 列: %s", p)
                return None
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date", ascending=True).reset_index(drop=True)
            return df
        except Exception as e:
            logger.warning("读取缓存失败 %s: %s", p, e)
            return None

    def max_date(self, stock_code: str) -> Optional[pd.Timestamp]:
        """该股票缓存中的最大交易日期；无缓存或空则返回 None。"""
        df = self.read(stock_code)
        if df is None or df.empty:
            return None
        return df["date"].max()

    def write(self, stock_code: str, df: pd.DataFrame) -> bool:
        """
        将当前数据写入该股票缓存（覆盖）。
        要求 df 含 date 列，建议含 code 及标准列。
        """
        if df is None or df.empty:
            return False
        try:
            p = self._path(stock_code)
            p.parent.mkdir(parents=True, exist_ok=True)
            if "date" in df.columns:
                df = df.sort_values("date", ascending=True)
            df.to_csv(p, index=False, encoding="utf-8-sig")
            logger.debug("已写入缓存: %s 行 -> %s", len(df), p)
            return True
        except Exception as e:
            logger.warning("写入缓存失败 %s: %s", stock_code, e)
            return False

    def merge_and_write(self, stock_code: str, new_df: pd.DataFrame) -> bool:
        """
        将新数据与已有缓存按日期合并（新数据覆盖同日期），再写回。
        若尚无缓存，则直接写入 new_df。
        """
        if new_df is None or new_df.empty:
            return False
        if "date" not in new_df.columns:
            logger.warning("merge_and_write: new_df 缺少 date 列")
            return False
        existing = self.read(stock_code)
        if existing is None or existing.empty:
            return self.write(stock_code, new_df)
        new_df = new_df.copy()
        new_df["date"] = pd.to_datetime(new_df["date"])
        # 去掉已有里与新数据日期重叠的行，再拼接
        new_dates = set(new_df["date"].dt.normalize())
        existing = existing[~pd.to_datetime(existing["date"]).dt.normalize().isin(new_dates)]
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.sort_values("date", ascending=True).drop_duplicates(subset=["date"], keep="last")
        combined = combined.reset_index(drop=True)
        return self.write(stock_code, combined)
