# -*- coding: utf-8 -*-
"""
Tushare 缓存独立运行入口。

示例：
  # 预拉取交易日历（需配置 TUSHARE_TOKEN）
  python -m src.tushare_cache --prefetch-calendar

  # 预拉取指定股票日线并写入缓存
  python -m src.tushare_cache 600519 600900 --days 90

  # 指定缓存目录
  TUSHARE_CACHE_DIR=/data/tushare_cache python -m src.tushare_cache 600519
"""

import argparse
import logging
import sys
from pathlib import Path

# 确保项目根在 path 中
if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tushare_cache")


def main():
    parser = argparse.ArgumentParser(description="Tushare 独立缓存：本地优先，缺数据时从 API 拉取")
    parser.add_argument(
        "--prefetch-calendar",
        action="store_true",
        help="从 Tushare 拉取交易日历并写入缓存（需 TUSHARE_TOKEN）",
    )
    parser.add_argument(
        "codes",
        nargs="*",
        help="股票代码列表，如 600519 600900",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="拉取最近 N 天日线（默认 90）",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="缓存根目录，默认用环境变量 TUSHARE_CACHE_DIR 或 ./tushare_cache",
    )
    args = parser.parse_args()

    if args.prefetch_calendar:
        from src.tushare_cache import get_trading_calendar
        from src.config import get_config
        config = get_config()
        if not config.tushare_token:
            logger.error("未配置 TUSHARE_TOKEN，无法拉取交易日历")
            sys.exit(1)
        cal = get_trading_calendar()
        if cal.fetch_and_save_from_tushare(config.tushare_token):
            logger.info("交易日历预拉取完成")
        else:
            logger.error("交易日历预拉取失败")
            sys.exit(1)
        return

    if args.cache_dir:
        import os
        os.environ["TUSHARE_CACHE_DIR"] = args.cache_dir

    if not args.codes:
        parser.print_help()
        logger.info("未指定股票代码，仅打印帮助。可执行: python -m src.tushare_cache 600519 600900")
        return

    from src.tushare_cache import TushareCacheService
    svc = TushareCacheService()
    for code in args.codes:
        try:
            df, from_cache = svc.get_daily_data(code, days=args.days)
            if df is not None and not df.empty:
                logger.info("%s: 共 %d 条，来源=%s", code, len(df), "本地缓存" if from_cache else "API")
            else:
                logger.warning("%s: 无数据", code)
        except Exception as e:
            logger.exception("%s: 失败 %s", code, e)


if __name__ == "__main__":
    main()
