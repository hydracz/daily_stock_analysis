# -*- coding: utf-8 -*-
"""
===================================
日线数据历史存储 - 写入 analysis_history 对应子目录
===================================

职责：
1. 将获取到的日线数据写入 analysis_history，与当前目录结构一致
2. 路径：analysis_history/{YYYY-MM-DD}/{code}/data/daily_{数据源}.csv
"""

import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import get_config

logger = logging.getLogger(__name__)


def _get_analysis_history_root() -> Path:
    """与 analysis_history 模块一致的根目录解析。"""
    config = get_config()
    root = getattr(config, "analysis_history_dir", None) or "analysis_history"
    path = Path(root)
    if not path.is_absolute():
        base = Path(__file__).resolve().parent.parent
        path = (base / root).resolve()
    return path


def _sanitize_source_name(source_name: str) -> str:
    """
    将数据源名称转为可作文件名的字符串。
    例如：AkshareFetcher -> akshare_fetcher，TushareFetcher -> tushare_fetcher
    """
    if not source_name or not source_name.strip():
        return "unknown"
    s = source_name.strip().lower()
    s = re.sub(r"[^\w]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"


def save_daily_data_to_history(
    df: pd.DataFrame,
    stock_code: str,
    source_name: str,
    fetch_date: Optional[date] = None,
) -> Optional[str]:
    """
    将日线数据写入 analysis_history：{analysis_history_dir}/{日期}/{code}/data/daily_{数据源}.csv

    Args:
        df: 日线 DataFrame（需含 date 等标准列）
        stock_code: 股票代码
        source_name: 数据源名称（如 AkshareFetcher、TushareFetcher）
        fetch_date: 获取日期，默认今天

    Returns:
        写入的文件路径（绝对路径），失败返回 None
    """
    try:
        config = get_config()
        if not getattr(config, "enable_data_history", True):
            return None

        root = _get_analysis_history_root()
        d = fetch_date or date.today()
        date_str = d.strftime("%Y-%m-%d")
        source_safe = _sanitize_source_name(source_name)

        # 与 analysis_history 一致：{根目录}/{日期}/{代码}/data/daily_{数据源}.csv
        dir_path = root / date_str / str(stock_code) / "data"
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / f"daily_{source_safe}.csv"

        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        logger.debug(f"[DataHistory] 已写入: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.warning(f"[DataHistory] 写入历史失败 {stock_code} @ {source_name}: {e}")
        return None
