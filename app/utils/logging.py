import uuid
import time
import logging
import structlog
from flask import request, g, has_request_context

def setup_logger(app):
    """
    Configures structlog to output structured JSON logs,
    integrates request ID tracing middleware, and tracks latency metrics.
    """
    # Configure the standard library logging to pipe into structlog
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if app.config.get("DEBUG") or app.config.get("TESTING"):
        # Local Development: Render logs nicely to standard console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: Format logs as clean structured JSON logs for log drains
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Register request tracing & latency tracking hooks
    @app.before_request
    def before_request_logging():
        g.start_time = time.time()
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Bind the current tracing request variables into active logging context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=g.request_id,
            path=request.path,
            method=request.method,
            ip=request.remote_addr or "0.0.0.0"
        )

    @app.after_request
    def after_request_logging(response):
        if not has_request_context() or not hasattr(g, "start_time"):
            return response
            
        duration_ms = (time.time() - g.start_time) * 1000.0
        response.headers['X-Request-ID'] = getattr(g, "request_id", "N/A")
        
        # Log request completion with duration and status details
        log = structlog.get_logger("request_tracker")
        log.info(
            "API Request Processed",
            status_code=response.status_code,
            latency_ms=round(duration_ms, 2)
        )
        return response

    @app.teardown_request
    def teardown_request_cleanup(exception=None):
        structlog.contextvars.clear_contextvars()
