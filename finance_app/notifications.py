"""Simple notification system."""

from tkinter import messagebox


def notify(title: str, message: str, master=None):
    try:
        messagebox.showinfo(title, message, parent=master)
    except Exception:
        # Fallback to print in environments without a display
        print(f"{title}: {message}")


def notify_warning(title: str, message: str, master=None):
    """Display a warning message."""
    try:
        messagebox.showwarning(title, message, parent=master)
    except Exception:
        print(f"{title} WARNING: {message}")
