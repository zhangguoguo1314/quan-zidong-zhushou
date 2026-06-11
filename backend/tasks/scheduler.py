from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from core.database import SessionLocal
from models.task import Task
from models.log import Log

scheduler = AsyncIOScheduler()


def run_task(task_id: int):
    """Execute a sign-in task"""
    asyncio.create_task(execute_task(task_id))


async def execute_task(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != "enabled":
            return

        task.last_run = datetime.utcnow()
        db.commit()

        account = task.account
        site = account.site

        result = await perform_sign_in(account, site)

        log = Log(
            task_id=task_id,
            result=str(result),
            status="success" if result.get("success") else "failed"
        )
        db.add(log)
        db.commit()

        if not result.get("success"):
            await send_notification(account, result)

    except Exception as e:
        log = Log(
            task_id=task_id,
            result=str(e),
            status="failed"
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


async def perform_sign_in(account, site):
    """Perform the actual sign-in using Playwright"""
    try:
        from services.scraper import ScraperService
        scraper = ScraperService()
        return await scraper.sign_in(account, site)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def send_notification(account, result):
    """Send email notification on failure"""
    try:
        from services.notification import NotificationService
        notification = NotificationService()
        await notification.send_failure_notification(account, result)
    except Exception:
        pass


def add_task(task_id: int, cron_expr: str):
    """Add a task to the scheduler"""
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(
        run_task,
        trigger=trigger,
        args=[task_id],
        id=str(task_id),
        replace_existing=True
    )


def remove_task(task_id: int):
    """Remove a task from the scheduler"""
    scheduler.remove_job(job_id=str(task_id))


def start_scheduler():
    """Start the scheduler with all enabled tasks"""
    db = SessionLocal()
    try:
        enabled_tasks = db.query(Task).filter(Task.status == "enabled").all()
        for task in enabled_tasks:
            add_task(task.id, task.cron)
        scheduler.start()
    finally:
        db.close()


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
