from __future__ import annotations

from .task_store import TaskStore


def _task_select_sql() -> str:
    return """
        SELECT
            task.id,
            task.animal_id,
            animal.name AS animal_name,
            task.title,
            task.description,
            task.recurrence_type,
            task.recurrence_interval,
            task.start_date,
            task.end_date,
            task.due_time,
            task.is_active,
            task.created_at,
            task.updated_at,
            (
                SELECT MIN(occurrence.scheduled_for)
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = task.id
                  AND occurrence.status = 'pending'
            ) AS next_pending_at,
            (
                SELECT COUNT(*)
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = task.id
                  AND occurrence.status = 'pending'
            ) AS pending_count,
            (
                SELECT COUNT(*)
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = task.id
                  AND occurrence.status = 'pending'
                  AND (
                      (
                          task.due_time IS NOT NULL
                          AND occurrence.scheduled_for < ?1
                      )
                      OR
                      (
                          task.due_time IS NULL
                          AND datetime(occurrence.scheduled_for, '+1 day') <= datetime(?1)
                      )
                  )
            ) AS overdue_count
        FROM tasks AS task
        LEFT JOIN animals AS animal ON animal.id = task.animal_id
    """


def apply_task_stabilization() -> None:
    """Apply backwards-compatible task fixes before TaskStore instances are used."""
    TaskStore._task_select_sql = staticmethod(_task_select_sql)
