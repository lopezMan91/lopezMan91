"""Simple notification system."""

import logging
from tkinter import messagebox


logger = logging.getLogger(__name__)


def notify(title: str, message: str, master=None):
    try:
        messagebox.showinfo(title, message, parent=master)
    except Exception:
        # Fallback for headless environments with structured logging.
        logger.info("ui_notification_fallback", extra={"title": title, "message": message})
