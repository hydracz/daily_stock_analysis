# -*- coding: utf-8 -*-
"""
===================================
用户自定义任务服务
===================================

职责：
1. 管理用户自定义任务配置
2. 按计划执行用户自定义分析任务
3. 用户股票清单覆盖 .env STOCK_LIST
"""

import logging
import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage import get_db
from src.models import User, UserCustomTask
from src.user_service import get_user_service

logger = logging.getLogger(__name__)


def _normalize_stock_list(value: str) -> str:
    """规范化股票列表"""
    parts = [p.strip() for p in value.replace("\n", ",").split(",")]
    parts = [p for p in parts if p]
    return ",".join(parts)


def _parse_stock_codes(stock_list_str: str) -> List[str]:
    """解析股票列表为代码列表"""
    if not stock_list_str or not stock_list_str.strip():
        return []
    return _normalize_stock_list(stock_list_str).split(",")


class CustomTaskService:
    """用户自定义任务服务"""

    def __init__(self):
        self.db = get_db()
        self.user_service = get_user_service()

    def get_user_custom_task(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户的自定义任务配置"""
        with self.db.get_session() as session:
            task = session.execute(
                select(UserCustomTask).where(UserCustomTask.user_id == user_id)
            ).scalar_one_or_none()
            if task:
                return task.to_dict()
        return None

    def save_user_custom_task(
        self,
        user_id: int,
        stock_list: str,
        schedule_time: str = "18:00",
        report_type: str = "simple",
        enabled: bool = True
    ) -> bool:
        """
        保存用户自定义任务配置

        Args:
            user_id: 用户ID
            stock_list: 股票列表（逗号或换行分隔）
            schedule_time: 每日执行时间 HH:MM
            report_type: full 或 simple
            enabled: 是否启用
        """
        # 验证 schedule_time 格式
        if not re.match(r'^\d{1,2}:\d{2}$', schedule_time):
            schedule_time = "18:00"
        # 解析并验证小时分钟
        try:
            h, m = map(int, schedule_time.split(":"))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                schedule_time = "18:00"
        except (ValueError, TypeError):
            schedule_time = "18:00"

        report_type = report_type.lower() if report_type else "simple"
        if report_type not in ("full", "simple"):
            report_type = "simple"

        normalized_stock = _normalize_stock_list(stock_list)

        with self.db.get_session() as session:
            task = session.execute(
                select(UserCustomTask).where(UserCustomTask.user_id == user_id)
            ).scalar_one_or_none()

            if task:
                task.stock_list = normalized_stock
                task.schedule_time = schedule_time
                task.report_type = report_type
                task.enabled = enabled
                task.updated_at = datetime.now()
            else:
                task = UserCustomTask(
                    user_id=user_id,
                    stock_list=normalized_stock,
                    schedule_time=schedule_time,
                    report_type=report_type,
                    enabled=enabled
                )
                session.add(task)

            session.commit()
            logger.info(f"[CustomTaskService] 保存用户 {user_id} 自定义任务: {schedule_time} {report_type}")
            return True

    def get_tasks_due_now(self) -> List[Tuple[int, UserCustomTask]]:
        """
        获取当前时刻应执行的任务列表

        每分钟检查一次，匹配 HH:MM
        """
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.date()

        result = []
        with self.db.get_session() as session:
            # 管理员默认可执行自定义任务，普通用户需开启 can_custom_task
            from sqlalchemy import or_
            tasks = session.execute(
                select(UserCustomTask, User)
                .join(User, UserCustomTask.user_id == User.id)
                .where(
                    UserCustomTask.enabled == True,
                    User.enabled == True,
                    or_(User.can_custom_task == True, User.is_admin == True),
                    UserCustomTask.schedule_time == current_time
                )
            ).all()

            for task, user in tasks:
                # 跳过空股票列表
                if not (task.stock_list or "").strip():
                    continue
                # 避免同一天重复执行
                if task.last_run_at and task.last_run_at.date() == today:
                    continue
                result.append((user.id, task))

        return result

    def mark_task_run(self, user_id: int) -> None:
        """标记任务已执行"""
        with self.db.get_session() as session:
            task = session.execute(
                select(UserCustomTask).where(UserCustomTask.user_id == user_id)
            ).scalar_one_or_none()
            if task:
                task.last_run_at = datetime.now()
                task.updated_at = datetime.now()
                session.commit()

    def run_user_custom_task(self, user_id: int) -> Dict[str, Any]:
        """
        执行用户自定义任务

        使用用户配置的股票列表、报告类型，依次分析并推送
        """
        task = self.get_user_custom_task(user_id)
        if not task or not task.get("enabled") or not task.get("stock_list"):
            return {"success": False, "error": "任务未配置或未启用"}

        codes = _parse_stock_codes(task["stock_list"])
        if not codes:
            return {"success": False, "error": "股票列表为空"}

        report_type = task.get("report_type") or "simple"
        from web.services import get_analysis_service
        analysis_service = get_analysis_service()

        submitted = []
        for code in codes:
            code = code.strip()
            if not code:
                continue
            try:
                result = analysis_service.submit_analysis(
                    code,
                    report_type=report_type,
                    force_refresh=False
                )
                if result.get("success"):
                    submitted.append({"code": code, "task_id": result.get("task_id")})
            except Exception as e:
                logger.warning(f"[CustomTaskService] 提交 {code} 分析失败: {e}")

        self.mark_task_run(user_id)
        return {
            "success": True,
            "message": f"已提交 {len(submitted)} 只股票分析",
            "submitted": submitted
        }


_custom_task_service: Optional[CustomTaskService] = None


def get_custom_task_service() -> CustomTaskService:
    """获取自定义任务服务实例"""
    global _custom_task_service
    if _custom_task_service is None:
        _custom_task_service = CustomTaskService()
    return _custom_task_service
