from __future__ import annotations

from .policy_import import import_and_post_policies
from .transactions import TransactionManager


class ImportExport:
    """Headless import/export service.

    GUI dialogs were removed to keep finance_app as reusable backend library.
    """

    def __init__(self, manager: TransactionManager, master=None):
        self.manager = manager
        self.master = master

    def import_csv(self, file_path: str):
        self.manager.import_csv(file_path)

    def import_policies(self, file_path: str):
        return import_and_post_policies(file_path, self.manager)

    def export_csv(self, file_path: str):
        self.manager.export_csv(file_path)

    def import_csv_dialog(self):
        raise RuntimeError("Tkinter UI removed. Use import_csv(file_path) or Odoo flows.")

    def import_policies_dialog(self):
        raise RuntimeError("Tkinter UI removed. Use import_policies(file_path) or Odoo flows.")

    def export_csv_dialog(self):
        raise RuntimeError("Tkinter UI removed. Use export_csv(file_path) or Odoo flows.")
