"""Import and export helper for CSV files."""

from tkinter import filedialog, messagebox
from .transactions import TransactionManager, Transaction

class ImportExport:
    """Handle CSV import/export with simple dialogs."""

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

    def export_summary_dialog(self):
        """Export a basic summary by category to a CSV file."""
        file_path = filedialog.asksaveasfilename(
            parent=self.master,
            title='Export Summary',
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')]
        )
        if file_path:
            try:
                summary = self.manager.summary_by_category()
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['category', 'spent'])
                    for cat, spent in summary.items():
                        writer.writerow([cat, spent])
                messagebox.showinfo('Export', 'Export successful')
            except Exception as e:
                messagebox.showerror('Export failed', str(e))
