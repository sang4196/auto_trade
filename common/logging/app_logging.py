from __future__ import annotations

import contextvars
import json
import logging
import logging.config
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


LogFormat = Literal["console", "json"]


_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id",
    default=None,
)

_job_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "job_id",
    default=None,
)


class ContextFilter(logging.Filter):
    """
    contextvars에 저장된 값을 LogRecord에 주입합니다.

    예:
        set_log_context(request_id="req-123")
        logger.info("hello")
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        record.trace_id = _trace_id.get()
        record.job_id = _job_id.get()
        return True


class JsonFormatter(logging.Formatter):
    """
    구조화된 JSON 로그 포매터입니다.

    서버, 배치, 크롤러, 자동매매 봇, 백엔드 서비스 등에서
    로그 수집 시스템과 연동하기 좋습니다.
    """

    RESERVED_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def formatTime(
        self,
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()

        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        request_id = getattr(record, "request_id", None)
        trace_id = getattr(record, "trace_id", None)
        job_id = getattr(record, "job_id", None)

        if request_id:
            payload["request_id"] = request_id

        if trace_id:
            payload["trace_id"] = trace_id

        if job_id:
            payload["job_id"] = job_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self.RESERVED_ATTRS
            and not key.startswith("_")
            and key not in payload
            and key not in {"request_id", "trace_id", "job_id"}
        }

        if extra:
            payload["extra"] = extra

        return json.dumps(payload, ensure_ascii=False, default=str)


def set_log_context(
    *,
    request_id: str | None = None,
    trace_id: str | None = None,
    job_id: str | None = None,
) -> None:
    """
    현재 실행 컨텍스트에 로그용 메타데이터를 설정합니다.

    FastAPI, Flask, Celery, APScheduler, 자동매매 루프,
    배치 잡 등에서 유용합니다.
    """

    if request_id is not None:
        _request_id.set(request_id)

    if trace_id is not None:
        _trace_id.set(trace_id)

    if job_id is not None:
        _job_id.set(job_id)


def clear_log_context() -> None:
    """
    현재 실행 컨텍스트의 로그 메타데이터를 초기화합니다.
    """

    _request_id.set(None)
    _trace_id.set(None)
    _job_id.set(None)


def setup_logging(
    *,
    level: str = "INFO",
    log_dir: str | Path = "logs",
    app_name: str = "app",
    log_format: LogFormat = "console",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
    disable_existing_loggers: bool = False,
) -> None:
    """
    애플리케이션 로깅 설정을 초기화합니다.

    Args:
        level:
            DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_dir:
            로그 파일이 저장될 디렉터리
        app_name:
            로그 파일명 prefix
        log_format:
            "console" 또는 "json"
        max_bytes:
            로그 파일 하나의 최대 크기
        backup_count:
            보관할 백업 로그 파일 개수
        disable_existing_loggers:
            외부 라이브러리 로거 비활성화 여부
    """

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    normalized_level = level.upper()

    console_formatter = {
        "format": (
            "%(asctime)s | %(process)d | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        ),
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    json_formatter = {
        "()": JsonFormatter,
    }

    formatter_name = "json" if log_format == "json" else "console"

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": disable_existing_loggers,
        "filters": {
            "context": {
                "()": ContextFilter,
            },
        },
        "formatters": {
            "console": console_formatter,
            "json": json_formatter,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": normalized_level,
                "formatter": formatter_name,
                "filters": ["context"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": normalized_level,
                "formatter": "json",
                "filters": ["context"],
                "filename": str(log_path / f"{app_name}.log"),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filters": ["context"],
                "filename": str(log_path / f"{app_name}.error.log"),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": normalized_level,
            "handlers": ["console", "file", "error_file"],
        },
        "loggers": {
            "urllib3": {
                "level": "WARNING",
                "propagate": True,
            },
            "requests": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    표준적인 logger getter입니다.

    사용 예:
        logger = get_logger(__name__)
    """

    return logging.getLogger(name)

def run_job() -> None:
    setup_logging(
        level="INFO",
        app_name="my_app",
        log_format="console",
    )
    print(__name__)
    logger = get_logger(__name__)

    set_log_context(job_id="daily-job-001")

    try:
        logger.info("작업을 시작합니다.")
        logger.info("데이터를 처리합니다.", extra={"count": 100})
        raise RuntimeError("예시 에러입니다.")

    except Exception:
        logger.exception("작업 처리 중 예외가 발생했습니다.")

    finally:
        clear_log_context()

if __name__ == "__main__":
    run_job()