from tkinter import filedialog, messagebox

from .policy_import import import_and_post_policies
from .transactions import TransactionManager


class ImportExport:
    def __init__(self, manager: TransactionManager, master=None):
        self.manager = manager
        self.master = master

    def import_csv_dialog(self):
        file_path = filedialog.askopenfilename(
            parent=self.master,
            title='Import CSV',
            filetypes=[('CSV files', '*.csv')]
        )
        if file_path:
            try:
                self.manager.import_csv(file_path)
                messagebox.showinfo('Import', 'Import successful')
            except Exception as e:
                messagebox.showerror('Import failed', str(e))

    def import_policies_dialog(self):
        file_path = filedialog.askopenfilename(
            parent=self.master,
            title='Importar pólizas',
            filetypes=[('Excel files', '*.xlsx'), ('CSV files', '*.csv')],
        )
        if file_path:
            try:
                result = import_and_post_policies(file_path, self.manager)
                messagebox.showinfo(
                    'Pólizas posteadas',
                    (
                        f"Pólizas posteadas: {result.policies_posted}\n"
                        f"Líneas leídas: {result.lines_read}\n"
                        f"Líneas posteadas: {result.lines_posted}"
                    ),
                )
            except Exception as e:
                messagebox.showerror('Posteo de pólizas fallido', str(e))

    def export_csv_dialog(self):
        file_path = filedialog.asksaveasfilename(
            parent=self.master,
            title='Export CSV',
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')]
        )
        if file_path:
            try:
                self.manager.export_csv(file_path)
                messagebox.showinfo('Export', 'Export successful')
            except Exception as e:
                messagebox.showerror('Export failed', str(e))
