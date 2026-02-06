# Tushare 独立缓存

本地优先的 Tushare 日线缓存：有数据且覆盖到「最新交易日」则直接返回，减少对外部 API 的依赖；缺数据或数据不是最新时用 API 拉取并写入缓存。非交易日通过交易日历排除。

## 缺数据情形

1. **该股票代码没有数据**：API 返回空，不写缓存，返回空或走其它数据源。
2. **该股票有数据但不是最新**：缓存中最大日期早于「最新交易日」时，会从 API 拉取缺失区间并合并写入缓存。
3. **非交易日**：以「最新交易日」为准（排除周末与法定节假日），不会把今天当「最新」若今天休市。

## 配置

| 环境变量 | 说明 | 默认 |
|----------|------|------|
| `ENABLE_TUSHARE_CACHE` | 是否启用 Tushare 缓存 Fetcher（优先从本地返回） | `false` |
| `TUSHARE_CACHE_DIR` | 缓存根目录 | `./tushare_cache` |
| `TUSHARE_TOKEN` | Tushare Pro Token（缺数据时拉取必填） | - |

启用后，`DataFetcherManager` 会加入 `TushareCachedFetcher`，优先级高于普通 `TushareFetcher`。

## 缓存目录结构

```
tushare_cache/
├── .calendar.csv          # 交易日历（可选，由 Tushare trade_cal 拉取）
└── {stock_code}/
    └── daily.csv          # 该股票日线（code, date, open, high, low, close, volume, amount, pct_chg 等）
```

## 交易日历

- **有缓存**：从 `tushare_cache/.calendar.csv` 读取（需先执行一次「预拉取」或由服务在首次使用时用 Token 拉取）。
- **无缓存**：退化为仅排除**周六、周日**；法定节假日需依赖 Tushare 的 `trade_cal` 拉取并写入 `.calendar.csv`。

## 独立运行

不依赖主分析流程，可单独用来预拉取日历或预填缓存：

```bash
# 预拉取交易日历（需配置 TUSHARE_TOKEN）
python -m src.tushare_cache --prefetch-calendar

# 预拉取指定股票日线并写入缓存
python -m src.tushare_cache 600519 600900 --days 90

# 指定缓存目录
TUSHARE_CACHE_DIR=/data/tushare_cache python -m src.tushare_cache 600519
```

## 作为库使用

```python
from src.tushare_cache import TushareCacheService, get_latest_trading_day, is_trading_day

svc = TushareCacheService()
df, from_cache = svc.get_daily_data("600519", days=90)
# from_cache True=本次完全来自本地，False=有从 API 拉取并已写入缓存

latest = get_latest_trading_day()  # 今日及之前的最近一个交易日
is_trading_day(latest)  # True

# 查看本进程内从 Tushare API 拉取的数据量（缓存到前天、再次运行后可看本次拉了多少）
stats = svc.get_fetch_stats()
# {"api_calls": 2, "api_rows": 2, "api_codes": ["600519", "600900"]}
```

通过 DataFetcherManager 运行时，分析结束后可查看本次运行的 Tushare API 拉取量：

```python
stats = fetcher_manager.get_tushare_cache_fetch_stats()
# 若使用了 TushareCachedFetcher 则返回 {"api_calls": N, "api_rows": M, "api_codes": [...]}，否则 None
```

主流程「分析完成」时会在日志中自动打印一行，例如：  
`Tushare 缓存本次运行 API 拉取: 调用 3 次，共 3 条数据（股票: 600519, 600900, 000001）`

## 与现有分析流程的关系

- **未启用**（`ENABLE_TUSHARE_CACHE=false`）：行为与之前一致，仅使用现有 `TushareFetcher` 等数据源。
- **启用**（`ENABLE_TUSHARE_CACHE=true`）：在数据源列表中增加 `TushareCachedFetcher`，获取日线时优先走缓存；缺数据或非最新时再调 Tushare API，并写入 `TUSHARE_CACHE_DIR`。
