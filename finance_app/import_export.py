from tkinter import filedialog, messagebox
from .transactions import TransactionManager, Transaction

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
