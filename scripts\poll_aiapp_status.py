import json
import os
import subprocess
import sys
import time


POLL_INTERVAL = 30
HEARTBEAT_INTERVAL = 300
MAX_WAIT_SECONDS = 3600
ACTIVE_STATUSES = {"queued", "running", "pending", "processing"}


def emit(kind: str, **kwargs) -> None:
    print(json.dumps({"kind": kind, **kwargs}, ensure_ascii=False), flush=True)


def query(task_id: str) -> dict | None:
    result = subprocess.run(
        ["dws", "aiapp", "query", "--task-id", task_id, "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        emit(
            "query_error",
            taskId=task_id,
            stderr=result.stderr.strip(),
            stdout=result.stdout.strip(),
        )
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        emit("parse_error", taskId=task_id, error=str(exc), raw=result.stdout.strip())
        return None


def normalize_payload(payload: dict) -> dict:
    task = payload.get("result") or payload.get("data") or payload
    result = task.get("result") if isinstance(task, dict) else {}
    if not isinstance(result, dict):
        result = {}
    return {
        "success": payload.get("success"),
        "taskId": task.get("taskId") or payload.get("taskId"),
        "status": str(task.get("status") or payload.get("status") or "").lower(),
        "threadId": task.get("threadId") or payload.get("threadId") or result.get("threadId"),
        "threadTitle": result.get("threadTitle") or task.get("threadTitle"),
        "threadViewUrl": task.get("threadViewUrl") or payload.get("threadViewUrl") or result.get("threadViewUrl"),
        "appPreviewUrl": result.get("appPreviewUrl") or task.get("appPreviewUrl") or payload.get("appPreviewUrl"),
        "message": task.get("message") or task.get("errorMessage") or payload.get("message") or payload.get("errorMessage"),
        "rawThreadStatus": task.get("rawThreadStatus"),
        "rawRunStatus": task.get("rawRunStatus"),
        "updatedAt": task.get("updatedAt"),
        "createdAt": task.get("createdAt"),
    }


def main() -> int:
    task_id = os.environ["TASK_ID"]
    thread_id = os.environ.get("THREAD_ID", "")
    thread_view_url = os.environ.get("THREAD_VIEW_URL", "")

    start = time.time()
    last_heartbeat = 0.0
    emit(
        "polling_started",
        taskId=task_id,
        threadId=thread_id,
        threadViewUrl=thread_view_url,
    )

    while True:
        payload = query(task_id)
        now = time.time()
        if payload:
            normalized = normalize_payload(payload)
            status = normalized["status"]
            latest_thread_id = normalized["threadId"] or thread_id
            latest_thread_view_url = normalized["threadViewUrl"] or thread_view_url
            app_preview_url = normalized["appPreviewUrl"]
            thread_title = normalized["threadTitle"]

            if not status:
                emit(
                    "unexpected_payload",
                    taskId=task_id,
                    payload=payload,
                )
                return 2

            if status == "succeeded":
                emit(
                    "task_succeeded",
                    taskId=task_id,
                    threadId=latest_thread_id,
                    threadViewUrl=latest_thread_view_url,
                    appPreviewUrl=app_preview_url,
                    threadTitle=thread_title,
                    rawThreadStatus=normalized["rawThreadStatus"],
                    rawRunStatus=normalized["rawRunStatus"],
                )
                return 0
            if status == "failed":
                emit(
                    "task_failed",
                    taskId=task_id,
                    threadId=latest_thread_id,
                    threadViewUrl=latest_thread_view_url,
                    message=normalized["message"],
                    rawThreadStatus=normalized["rawThreadStatus"],
                    rawRunStatus=normalized["rawRunStatus"],
                )
                return 1
            if status in ACTIVE_STATUSES and now - last_heartbeat >= HEARTBEAT_INTERVAL:
                emit(
                    "task_heartbeat",
                    taskId=task_id,
                    status=status,
                    elapsedSeconds=int(now - start),
                    threadId=latest_thread_id,
                    threadViewUrl=latest_thread_view_url,
                    rawThreadStatus=normalized["rawThreadStatus"],
                    rawRunStatus=normalized["rawRunStatus"],
                    updatedAt=normalized["updatedAt"],
                )
                last_heartbeat = now

        if now - start >= MAX_WAIT_SECONDS:
            emit(
                "task_timeout",
                taskId=task_id,
                elapsedSeconds=int(now - start),
                threadId=thread_id,
                threadViewUrl=thread_view_url,
            )
            return 124

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
