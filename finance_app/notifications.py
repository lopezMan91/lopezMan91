"""Notification helpers without GUI dependencies (headless-safe)."""

import logging


logger = logging.getLogger(__name__)


def notify(title: str, message: str, master=None):
    _ = master
    logger.info("notification", extra={"title": title, "message": message})
