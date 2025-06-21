import tkinter as tk
from tkinter import ttk, messagebox
from .transactions import Transaction, TransactionManager
from .budget import Budget
from .import_export import ImportExport
from .analysis import Analysis
from .goals import Goal, GoalManager
from .notifications import notify, notify_warning
from .user import UserManager
from .api import get_exchange_rate


class LoginDialog(tk.Toplevel):
    """Simple login and registration dialog."""

    def __init__(self, master: tk.Tk, user_manager: UserManager):
        super().__init__(master)
        self.user_manager = user_manager
        self.title("Login")
        self.resizable(False, False)
        self.success = False

        ttk.Label(self, text="Usuario:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(self, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.user_var).grid(row=0, column=1, padx=5)
        ttk.Entry(self, textvariable=self.pass_var, show="*").grid(row=1, column=1, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Ingresar", command=self.do_login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Registrar", command=self.do_register).pack(side=tk.LEFT, padx=5)

    def do_login(self):
        if self.user_manager.login(self.user_var.get(), self.pass_var.get()):
            self.success = True
            self.destroy()
        else:
            messagebox.showerror("Login", "Credenciales invalidas", parent=self)

    def do_register(self):
        if self.user_manager.register(self.user_var.get(), self.pass_var.get()):
            messagebox.showinfo("Registro", "Usuario registrado", parent=self)
        else:
            messagebox.showerror("Registro", "El usuario ya existe", parent=self)

class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Finance Manager')
        self.geometry('600x400')

        self.user_manager = UserManager()
        if not self.login_flow():
            # Close the app if login was cancelled or failed
            self.destroy()
            return

        self.manager = TransactionManager()
        self.budget = Budget()
        self.import_export = ImportExport(self.manager, self)
        self.analysis = Analysis(self.manager)
        self.goals = GoalManager()

        self.create_widgets()

    def login_flow(self) -> bool:
        dialog = LoginDialog(self, self.user_manager)
        self.wait_window(dialog)
        return dialog.success

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
        export_summary_btn = ttk.Button(frame, text='Exportar Resumen', command=self.import_export.export_summary_dialog)
        export_summary_btn.grid(row=6, column=0, columnspan=2, pady=5)

        goal_btn = ttk.Button(frame, text='Agregar Meta', command=self.add_goal)
        goal_btn.grid(row=7, column=0, columnspan=2, pady=5)

        show_goals_btn = ttk.Button(frame, text='Ver Metas', command=self.show_goals)
        show_goals_btn.grid(row=8, column=0, columnspan=2, pady=5)

        budget_btn = ttk.Button(frame, text='Limite Categoria', command=self.set_budget_limit)
        budget_btn.grid(row=9, column=0, columnspan=2, pady=5)
        rate_btn = ttk.Button(frame, text='Tipo de Cambio', command=self.show_exchange_rate)
        rate_btn.grid(row=10, column=0, columnspan=2, pady=5)
        summary_btn = ttk.Button(frame, text='Resumen', command=self.show_summary)
        summary_btn.grid(row=11, column=0, columnspan=2, pady=10)

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
        if amount < 0:
            spent = self.manager.spent_by_category(transaction.category)
            if self.budget.is_exceeded(transaction.category, spent):
                notify('Presupuesto', f'Limite para {transaction.category} excedido', master=self)
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

    def set_budget_limit(self):
        category = self.simple_prompt('Categoria:')
        if not category:
            return
        amount_str = self.simple_prompt('Limite:')
        if not amount_str:
            return
        try:
            amount = float(amount_str)
        except ValueError:
            notify('Error', 'Monto invalido', master=self)
            return
        self.budget.set_limit(category, amount)
        notify('Presupuesto', f'Limite establecido para {category}', master=self)

    def show_summary(self):
        ratio = self.analysis.expense_ratio() * 100
        message = self.analysis.summary() + f"\nPorcentaje de gastos: {ratio:.0f}%"
        messagebox.showinfo('Resumen', message)

    def show_exchange_rate(self):
        rate = get_exchange_rate()
        if rate:
            notify('Tipo de cambio', f'USD -> MXN: {rate:.2f}', master=self)
        else:
            notify_warning('Tipo de cambio', 'No disponible', master=self)

    def show_goals(self):
        if not self.goals.goals:
            message = 'No hay metas definidas'
        else:
            lines = [
                f"{g.name}: {g.saved_amount:.2f}/{g.target_amount:.2f} ({g.progress()*100:.0f}%)"
                for g in self.goals.goals
            ]
            message = "\n".join(lines)
        messagebox.showinfo('Metas', message)

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
