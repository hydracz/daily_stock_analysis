# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 分析历史存储
===================================

职责：
1. 按「股票代码 + 日期」存储分析结果，同一天内命中缓存则直接返回
2. 保存所有获取到的数据（分类）、报告内容、LLM 请求与响应
3. 目录存储规范，便于排查与复现

目录规范：
    analysis_history/           # 根目录（可在配置中修改）
    └── {YYYY-MM-DD}/           # 按日期
        └── {code}/             # 按股票代码，如 600519
            ├── meta.json       # 分析元信息：股票名、分析时间、是否成功
            ├── data/           # 获取到的数据（分类）
            │   ├── daily.json      # 日线/分析上下文（today、yesterday 等）
            │   ├── realtime.json   # 实时行情
            │   ├── chip.json      # 筹码分布
            │   ├── trend.json     # 趋势分析结果
            │   └── intel.txt      # 情报/新闻汇总文本
            ├── report.txt      # 生成的报告内容
            └── llm/
                ├── request.json   # 请求：prompt 摘要 + 长度等
                └── response.json  # 返回：raw_response + 解析结果摘要
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import get_config
from src.analyzer import AnalysisResult

logger = logging.getLogger(__name__)

# 历史根目录默认名
DEFAULT_HISTORY_DIR = "analysis_history"
# 命中缓存时标记
META_SUCCESS_KEY = "success"
META_ANALYZED_AT_KEY = "analyzed_at"
META_STOCK_NAME_KEY = "stock_name"
META_CODE_KEY = "code"
META_DATE_KEY = "date"


def _get_history_root() -> Path:
    """获取历史存储根目录（从配置或默认）。"""
    config = get_config()
    root = getattr(config, "analysis_history_dir", None) or DEFAULT_HISTORY_DIR
    path = Path(root)
    if not path.is_absolute():
        # 相对路径基于项目根目录
        base = Path(__file__).resolve().parent.parent
        path = (base / root).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_stock_date_dir(code: str, target_date: date) -> Path:
    """获取某股票某日期的存储目录。"""
    root = _get_history_root()
    date_str = target_date.isoformat()
    return root / date_str / code


def _meta_path(code: str, target_date: date) -> Path:
    """meta.json 路径。"""
    return _get_stock_date_dir(code, target_date) / "meta.json"


def is_history_enabled() -> bool:
    """是否启用分析历史（从配置读取）。"""
    config = get_config()
    return getattr(config, "enable_analysis_history", True)


def has_cached_analysis(code: str, target_date: Optional[date] = None) -> bool:
    """
    检查指定股票在指定日期是否已有成功分析缓存。

    Args:
        code: 股票代码
        target_date: 目标日期，默认当天

    Returns:
        若该日期下存在成功分析的 meta 且 success 为 True，则返回 True
    """
    if not is_history_enabled():
        return False
    if target_date is None:
        target_date = date.today()
    meta_file = _meta_path(code, target_date)
    if not meta_file.exists():
        return False
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return meta.get(META_SUCCESS_KEY, False) is True
    except Exception as e:
        logger.debug("读取历史 meta 失败 %s: %s", meta_file, e)
        return False


def load_cached_analysis(
    code: str,
    target_date: Optional[date] = None,
    report_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    从历史目录加载已缓存的分析结果。

    Args:
        code: 股票代码
        target_date: 目标日期，默认当天
        report_type: 报告类型（如 simple/full），用于读取 report_{report_type}.txt；不传则兼容旧版 report.txt

    Returns:
        包含 result、report_content（按 report_type）、data、meta 的字典；若不存在或读取失败则返回 None。
    """
    if target_date is None:
        target_date = date.today()
    base = _get_stock_date_dir(code, target_date)
    meta_file = base / "meta.json"
    if not meta_file.exists():
        return None
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if not meta.get(META_SUCCESS_KEY, False):
            return None

        # 加载分析结果（与 save 时结构一致）
        result = None
        result_file = base / "llm" / "response.json"
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                resp = json.load(f)
            parsed = resp.get("parsed") or resp.get("result")
            if parsed:
                result = AnalysisResult.from_dict(parsed)

        # 报告内容：按类型读取 report_{report_type}.txt，兼容旧版 report.txt
        report_content = ""
        if report_type:
            report_file = base / f"report_{report_type}.txt"
            if report_file.exists():
                report_content = report_file.read_text(encoding="utf-8")
        if not report_content:
            legacy = base / "report.txt"
            if legacy.exists():
                report_content = legacy.read_text(encoding="utf-8")

        # 各类数据（可选，供调试）
        data = {}
        data_dir = base / "data"
        if data_dir.exists():
            for name in ("daily", "realtime", "chip", "trend"):
                p = data_dir / f"{name}.json"
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        data[name] = json.load(f)
            intel_file = data_dir / "intel.txt"
            if intel_file.exists():
                data["intel"] = intel_file.read_text(encoding="utf-8")

        return {
            "result": result,
            "report_content": report_content,
            "data": data,
            "meta": meta,
        }
    except Exception as e:
        logger.warning("加载历史分析失败 %s: %s", base, e)
        return None


def save_analysis(
    code: str,
    target_date: date,
    *,
    result: AnalysisResult,
    report_contents: Optional[Dict[str, str]] = None,
    data_daily: Optional[Dict[str, Any]] = None,
    data_realtime: Optional[Dict[str, Any]] = None,
    data_chip: Optional[Dict[str, Any]] = None,
    data_trend: Optional[Dict[str, Any]] = None,
    data_intel: Optional[str] = None,
    llm_prompt: Optional[str] = None,
    llm_response: Optional[str] = None,
) -> Path:
    """
    将一次完整分析写入历史目录。

    Args:
        code: 股票代码
        target_date: 分析日期
        result: 分析结果对象
        report_contents: 按报告类型分开的报告文本，如 {"simple": "...", "full": "..."}，便于按类型读取
        data_daily: 日线/分析上下文（如 today、yesterday）
        data_realtime: 实时行情 dict
        data_chip: 筹码分布 dict
        data_trend: 趋势分析结果 dict
        data_intel: 情报/新闻汇总文本
        llm_prompt: 大模型请求 prompt 全文
        llm_response: 大模型返回原文

    Returns:
        该股票该日期的存储目录路径
    """
    if not is_history_enabled():
        return Path()
    base = _get_stock_date_dir(code, target_date)
    base.mkdir(parents=True, exist_ok=True)
    (base / "data").mkdir(exist_ok=True)
    (base / "llm").mkdir(exist_ok=True)

    # meta.json
    meta = {
        META_CODE_KEY: code,
        META_DATE_KEY: target_date.isoformat(),
        META_STOCK_NAME_KEY: getattr(result, "name", ""),
        META_SUCCESS_KEY: getattr(result, "success", True),
        META_ANALYZED_AT_KEY: datetime.now().isoformat(),
    }
    with open(base / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # data/
    if data_daily is not None:
        _safe_json_dump(base / "data" / "daily.json", data_daily)
    if data_realtime is not None:
        _safe_json_dump(base / "data" / "realtime.json", data_realtime)
    if data_chip is not None:
        _safe_json_dump(base / "data" / "chip.json", data_chip)
    if data_trend is not None:
        _safe_json_dump(base / "data" / "trend.json", data_trend)
    if data_intel is not None:
        (base / "data" / "intel.txt").write_text(data_intel, encoding="utf-8")

    # 按报告类型分开保存：report_simple.txt, report_full.txt 等，便于按类型读取
    if report_contents:
        for rtype, content in report_contents.items():
            if content:
                safe_name = (rtype or "report").replace("/", "_").strip() or "report"
                (base / f"report_{safe_name}.txt").write_text(content, encoding="utf-8")

    # llm/request.json, response.json
    if llm_prompt is not None:
        _safe_json_dump(
            base / "llm" / "request.json",
            {
                "prompt_length": len(llm_prompt),
                "prompt_preview": llm_prompt[:2000] + ("..." if len(llm_prompt) > 2000 else ""),
                "prompt_full": llm_prompt,
            },
        )
    if llm_response is not None:
        parsed = result.to_dict() if result else None
        _safe_json_dump(
            base / "llm" / "response.json",
            {"raw_response": llm_response, "parsed": parsed},
        )

    logger.info("分析历史已写入: %s", base)
    return base


def _safe_json_dump(path: Path, obj: Any) -> None:
    """安全写入 JSON，兼容不可序列化类型。"""
    def _default(o: Any) -> Any:
        if hasattr(o, "value"):  # Enum
            return o.value
        if hasattr(o, "isoformat"):  # date/datetime
            return o.isoformat()
        raise TypeError(type(o).__name__)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=_default)
