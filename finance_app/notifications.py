"""Simple notification system."""

from tkinter import messagebox


def notify(title: str, message: str, master=None):
    try:
        messagebox.showinfo(title, message, parent=master)
    except Exception:
        # Fallback to print in environments without a display
        print(f"{title}: {message}")
