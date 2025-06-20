import tkinter as tk
from tkinter import ttk, messagebox
from .transactions import Transaction, TransactionManager
from .budget import Budget
from .import_export import ImportExport
from .analysis import Analysis
from .goals import Goal, GoalManager
from .notifications import notify

class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Finance Manager')
        self.geometry('600x400')

        self.manager = TransactionManager()
        self.budget = Budget()
        self.import_export = ImportExport(self.manager, self)
        self.analysis = Analysis(self.manager)
        self.goals = GoalManager()

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(frame, text='Fecha:').grid(row=0, column=0)
        ttk.Label(frame, text='Descripcion:').grid(row=1, column=0)
        ttk.Label(frame, text='Monto:').grid(row=2, column=0)
        ttk.Label(frame, text='Categoria:').grid(row=3, column=0)

        self.date_entry = ttk.Entry(frame)
        self.desc_entry = ttk.Entry(frame)
        self.amount_entry = ttk.Entry(frame)
        self.category_entry = ttk.Entry(frame)

        self.date_entry.grid(row=0, column=1)
        self.desc_entry.grid(row=1, column=1)
        self.amount_entry.grid(row=2, column=1)
        self.category_entry.grid(row=3, column=1)

        add_btn = ttk.Button(frame, text='Agregar', command=self.add_transaction)
        add_btn.grid(row=4, column=0, columnspan=2, pady=5)

        import_btn = ttk.Button(frame, text='Importar CSV', command=self.import_export.import_csv_dialog)
        import_btn.grid(row=5, column=0, pady=5)
        export_btn = ttk.Button(frame, text='Exportar CSV', command=self.import_export.export_csv_dialog)
        export_btn.grid(row=5, column=1, pady=5)

        goal_btn = ttk.Button(frame, text='Agregar Meta', command=self.add_goal)
        goal_btn.grid(row=6, column=0, columnspan=2, pady=5)

        summary_btn = ttk.Button(frame, text='Resumen', command=self.show_summary)
        summary_btn.grid(row=7, column=0, columnspan=2, pady=10)

    def add_transaction(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror('Error', 'Monto invalido')
            return

        transaction = Transaction(
            date=self.date_entry.get(),
            description=self.desc_entry.get(),
            amount=amount,
            category=self.category_entry.get()
        )
        self.manager.add_transaction(transaction)
        messagebox.showinfo('Agregado', 'Transaccion agregada')
        self.date_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)

    def add_goal(self):
        name = self.simple_prompt('Nombre de la meta:')
        if not name:
            return
        target_str = self.simple_prompt('Monto objetivo:')
        if not target_str:
            return
        try:
            target = float(target_str)
        except ValueError:
            notify('Error', 'Monto invalido', master=self)
            return
        self.goals.add_goal(Goal(name=name, target_amount=target))
        notify('Meta', 'Meta agregada', master=self)

    def show_summary(self):
        messagebox.showinfo('Resumen', self.analysis.summary())

    def simple_prompt(self, message: str) -> str | None:
        top = tk.Toplevel(self)
        top.title(message)
        var = tk.StringVar()
        ttk.Entry(top, textvariable=var).pack(padx=10, pady=10)
        val = []

        def ok():
            val.append(var.get())
            top.destroy()

        ttk.Button(top, text='OK', command=ok).pack(pady=5)
        self.wait_window(top)
        return val[0] if val else None

if __name__ == '__main__':
    app = FinanceApp()
    app.mainloop()
