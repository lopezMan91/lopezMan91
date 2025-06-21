# Finance Manager

Simple personal finance application with a Tkinter GUI.

## Requisitos
- Python 3.8+
- `matplotlib` (solo para graficas futuras, no obligatorio)

## Uso
```bash
python -m finance_app.main
```

Puedes agregar transacciones, importar y exportar archivos CSV y ver un resumen rapido de tus finanzas. Tambien puedes definir metas de ahorro sencillas.

La interfaz ahora se organiza en pestañas para un acceso rapido a cada modulo y cuenta con una tabla interactiva para revisar las transacciones ingresadas.

Otras funciones incluidas en esta version:

- Gestor basico de metas financieras.
- Sistema de notificaciones simple.
- Control simple de presupuestos por categoria.
- Esqueleto de gestion de usuarios y consulta a la API de Banxico (sin depender de `requests`).
- Pantalla de inicio con registro e inicio de sesión básicos.
- Consulta rapida del tipo de cambio USD/MXN.
- Exportacion de resumen de gastos por categoria.
