import logging
import re


LOGGER_NAME = "finsight"
_SECRET_PATTERNS = [
    (re.compile(r"(mongodb\+srv://)([^:]+):([^@]+)(@)", re.IGNORECASE), r"\1\2:***\4"),
    (re.compile(r"\b(sk|hf|nvapi|AIza|AQ\.)[-A-Za-z0-9_.]+\b"), "***"),
]


def _redact(value):
    text = str(value)
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def get_logger():
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_event(level, event, **context):
    logger = get_logger()
    if context:
        safe_context = " ".join(
            f"{key}={_redact(value)}" for key, value in sorted(context.items())
        )
        message = f"{event} | {safe_context}"
    else:
        message = event
    getattr(logger, level.lower(), logger.info)(message)


def log_exception(event, exc, **context):
    logger = get_logger()
    safe_context = {key: _redact(value) for key, value in context.items()}
    if safe_context:
        logger.exception("%s | %s | error=%s", event, safe_context, _redact(exc))
    else:
        logger.exception("%s | error=%s", event, _redact(exc))
