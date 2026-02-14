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

Otras funciones incluidas en esta version:

- Gestor basico de metas financieras.
- Sistema de notificaciones simple.
- Esqueleto de gestion de usuarios y consulta a la API de Banxico.


## Importación y posteo de pólizas desde Excel

Ahora puedes importar pólizas contables desde archivos **.xlsx** o **.csv** (exportados de Excel) y postearlas automáticamente.

### Formato esperado de columnas

- `poliza`
- `fecha`
- `descripcion`
- `cuenta`
- `cargo`
- `abono`
- `categoria` (opcional)

### Regla de validación

Cada póliza debe cuadrar: **suma(cargo) == suma(abono)**.
Si una póliza no cuadra, el posteo se rechaza.

## Arquitectura mínima (multi-ledger + SAT + consolidación)

Se agregó una base de arquitectura para crecer en paralelo SAT/Estados/IFRS/Consolidación.

### Objetos base implementados

- `BusinessEvent`: evento de negocio inmutable.
- `PostingRun`: corrida del motor contable (versión de reglas + logs).
- `Ledger`: libros `LOCAL`, `IFRS`, `CONSOL`, `ELIM`.
- `JournalEntry`/`JournalLine`: pólizas por ledger y compañía.
- `FiscalDocument` + `FiscalVault`: CFDI (UUID, estatus SAT, hash) y vínculo póliza↔UUID↔evento.
- `ReportingTemplate`: mapeo cuenta→rubro por ledger para estados financieros.
- `ControlLibrary` + `SODRule`: base de controles y segregación de funciones.
- `ReconciliationWorkflow`: conciliaciones con evidencia y estatus.

### Caso end-to-end 1 (México)

1. Se captura un `BusinessEvent` de compra con CFDI.
2. `AccountingEngine` genera pólizas por ledger (Local/IFRS) con políticas versionadas.
3. `FiscalVault` liga `policy_id ↔ UUID ↔ event_id` y valida gates de cierre.
4. Se puede exportar la base para CE/DIOT en siguientes iteraciones.

### Caso end-to-end 2 (Grupo)

1. Se recibe TB/eventos de entidades y se postea a `IFRS`.
2. Se usan ledgers `CONSOL` y `ELIM` para preparar conversión/eliminaciones.
3. `FinancialStatementBuilder` publica Balance/P&L por plantilla y ledger con drilldown.

## Roadmap funcional sugerido

### Fase 0
- Core contable multi-ledger (ya base implementada)
- Builder básico Balance/P&L (ya base implementada)

### SAT (MVP)
- Fiscal Vault + validaciones de cierre (base implementada)
- Contabilidad electrónica (catálogo/balanza/pólizas XML)
- DIOT con bitácora de presentación

### IFRS + Consolidación (MVP)
- Ledger IFRS adjustment-only y full
- Conversión IAS 21 y eliminaciones AR/AP + ventas/COGS
- Reportes consolidados + puente Local→IFRS→Consolidado

## Épica 1 — Motor automático de arrendamientos (IFRS 16 + NIF D-5)

Se añadió `finance_app/lease_engine.py` con soporte base para:

- Captura única del contrato (`LeaseContract`) y calendario (`LeasePaymentSchedule`).
- Tasa de descuento (`LeaseDiscountRate`) con tipo: `implicit` / `IBR` / `risk_free`.
- Medición inicial (`LeaseMeasurementSnapshot`):
  - Pasivo = valor presente de pagos.
  - ROU = pasivo + prepagos + costos directos − incentivos + provisiones.
- Tabla de amortización periódica (`LeaseAmortizationLine`).
- Posteo automático mensual por ledger (`LeasePostingBatch`) con interés, depreciación y pago.
- Remeasurements por modificación (`LeaseModification` + `remeasure_contract`).

### Hard stops implementados
- Contrato sin pagos.
- Tasa no aprobada (`annual_rate <= 0`).
- Moneda de pagos inconsistente con la tasa.

## Épica 2 — Importador de pólizas por plantilla (Excel/CSV) con staging

Se añadió `finance_app/journal_importer.py` con flujo robusto:

1. **Carga** de archivo `.xlsx` o `.csv`.
2. **Staging** (`JournalImportStaging`) con preview por póliza.
3. **Validaciones duras** (antes de postear):
   - Cuadre débito/crédito por póliza
   - Ledger válido
   - Cuenta obligatoria
   - Partner obligatorio para cuentas 21xx
   - FX type cuando hay moneda distinta a MXN
4. **Aprobación** explícita.
5. **Posteo** a pólizas con idempotencia por `batch_id + ref + posting_date + ledger`.

### Plantilla de importación soportada

Campos principales:
`batch_id, company, ledger, journal, posting_date, document_date, ref, memo, currency, fx_rate_type, supporting_doc_id, line_no, account_code, partner, debit, credit, amount_currency, analytic_account, tags, tax_code, due_date, description`.

## Odoo addon base (nuevo)

Se agregó un addon inicial en `odoo_addons/mx_finance_core` para arrancar desde cero con arquitectura enterprise:

- Multi-ledger: Local/IFRS/Consolidation/Eliminations.
- Evento contable inmutable + posting runs.
- Fiscal Vault (UUID CFDI, estatus, hash, vínculo a póliza/evento).
- Tabla FX con lock de periodo.
- Plantillas de estados financieros.
- Estructura de grupo para consolidación.
- Base de arrendamientos IFRS16/NIF D-5.
- Staging para importación de pólizas (Excel/CSV).

Documentación de ejecución:
- `ODOO_BACKLOG_JIRA.md`
- `ODOO_DATA_MODEL_AND_FLOWS.md`

## Motor Fiscal México (base v1.2)

Se agregó `finance_app/tax_engine_mx.py` con una base funcional para cálculo fiscal línea por línea:

- Atributos fiscales por línea (`TaxLineAttributes`) con deducibilidad, IVA acreditable/no acreditable, retenciones y metadatos CFDI.
- Paquete de evidencia fiscal (`TaxEvidencePack`) con validación mínima para bloquear acreditamiento sin soporte.
- Motor IVA mensual (`TaxEngineMX.compute_iva_summary`) con salida de DIOT por proveedor y líneas bloqueadas.
- Conciliación ISR contable-fiscal (`compute_isr_reconciliation`) separando permanentes y temporales.
- Cálculo PTU con regla de tope legal por empleado (`compute_ptu_legal_for_employee`).
- Motor de diferidos (`TemporaryDifference`, `compute_deferred_tax_totals`) para DTA/DTL y neto.

Pruebas asociadas: `tests/test_tax_engine_mx.py`.

## Odoo audit-ready (fundamentos añadidos)

Se fortaleció `mx_finance_core` con capacidades base enterprise:

- Reglas contables versionadas (`mx.accounting.policy/version`).
- Gobierno de cierre y reaperturas auditables (`mx.close.period`, `mx.close.reopen.log`).
- Dimensiones y reglas de cuenta obligatorias (`mx.dimension`/`mx.dimension.value`, `mx.account.rule`).
- Trazabilidad intercompany (`mx.intercompany.tag`).
- Inventario de coberturas (`mx.hedge.instrument`).
- Paquetes de estados financieros con workflow (`mx.statement.package`).
- Staging line-level para importador de pólizas (`mx.journal.import.line`).

- `ODOO_RELEASE_PLAN.md`
- `ODOO_MENU_MAP_BY_ROLE.md`
- `ODOO_LOGICAL_DATA_MODEL.md`
- `ODOO_HARD_RULES_AND_JOBS.md`


## Intangibles (NIF C-8 / IAS 38) + Revenue IFRS 15 (base v1.3)

Se añadieron dos motores de base para ampliar cobertura NIF/IFRS:

- `finance_app/intangibles_engine.py`
  - Subledger lógico para intangibles con rollforward.
  - Flujo I+D con gate de capitalización (Investigación vs Desarrollo) y regla anti-recaptura.
  - Simulaciones de amortización, deterioro y clasificación SaaS/website (asset vs expense).
- `finance_app/revenue_ifrs15.py`
  - Motor de 5 pasos simplificado: asignación de precio por SSP, reconocimiento point-in-time/over-time.
  - Evaluación principal vs agente (bruto vs neto).
  - Rollforward de contrato (asset/liability), clasificación de licencias y warranties, modificación contractual.

Pruebas nuevas:
- `tests/test_intangibles_engine.py`
- `tests/test_revenue_ifrs15.py`



## Release 0 hardening (ledger-first + dimensions + posting preview)

Se reforzó la base Odoo (`mx_finance_core`) para alinear decisiones técnicas de arquitectura:

- **Ledger first-class**: validación de locks por periodo/ledger al postear (`account.move.action_post`) y unicidad de ledger por compañía.
- **Dimensiones empresariales**: campos explícitos en líneas (`mx_profit_center_id`, `mx_cost_center_id`) con validaciones por cuenta (`mx_require_profit_center`, `mx_require_cost_center`).
- **Posting engine governance**: `mx.posting.run` ahora soporta **Posting Preview** y guarda `preview_payload` auditable previo al posteo final.
- **Eventos multi-ledger**: `mx.accounting.event` ahora incluye `ledger_scope` para control explícito de alcance (Local/IFRS/Fiscal/Multi).



## Release 0.5 blueprint alignment (mx_account_core v1.5)

Se incorporaron piezas de datos/UI para el blueprint v1.5 de `mx_account_core`:

- Nuevo modelo de lock por rango `mx.account.period.lock` (company+ledger+date range, sin traslapes).
- Modelo de dimensiones enterprise normalizado:
  - `mx.dimension.type`
  - `mx.dimension.value`
  - `mx.dimension.set` (deduplicado por `hash_key`)
  - `mx.dimension.rule`
- Extensión GL con `dimension_set_id` en `account.move.line`.
- `mx.posting.run` con `input_hash` para idempotencia (además de preview payload).
- Menús y vistas iniciales para tipos/valores/sets/reglas de dimensión y locks por rango.



## Optimización y depuración reciente

- Se eliminó la carga de vistas de **dimensiones legacy** del manifest para reducir ruido funcional en UI.
- Se optimizó la validación de locks en `account.move` para evitar consultas N+1 (bulk load de locks por lote de pólizas).
- Se unificó captura de `profit center` / `cost center` sobre `mx.dimension.value` y autocompletado desde `dimension_set_id`, evitando catálogos paralelos inconsistentes.


## Auditoría técnica y estrés

- Reporte de auditoría técnica: `TECH_AUDIT.md`
- Script de estrés de importación masiva: `scripts/stress_test_journal_import.py`

Ejemplo:

```bash
python scripts/stress_test_journal_import.py --entries 50000
```


## Endurecimiento reciente (precisión, logging y controles)

- `lease_engine` ahora usa `Decimal` internamente para cálculos de VP/amortización y expone `validate_schedule_consistency` para control de cierre anual.
- `notifications.notify` migra fallback de `print()` a `logging` estructurado para trazabilidad en entornos headless.
- Se agregaron pruebas para detectar inconsistencias en la tabla de amortización (`tests/test_lease_engine.py`).


## Compliance y automatización avanzada (incremental)

- **Fiscal Vault reforzado**: `FiscalDocument` ahora contempla banderas LCO/EFOS para bloquear CFDI de riesgo durante gates de cierre.
- **Integridad de pólizas**: `JournalEntry` incluye hash de integridad y helper `verify_entry_integrity` para detectar alteraciones.
- **Conciliación inteligente**: `suggest_fuzzy_matches` combina similitud de descripción + tolerancia de monto para sugerir conciliaciones bancarias.
- **Sugerencia NLP heurística**: `suggest_account_and_cost_center` propone cuenta/centro de costo por palabras clave (con confianza y justificación).

> Nota: SSO (Azure AD / Google Workspace) y MFA deben implementarse en la capa de despliegue/autenticación (Odoo auth/provider) y no en estos módulos puros de dominio.


## Refuerzo normativo y gobernanza (incremental)

- **Selector de principio dominante por ledger** en motor contable (`NIF`, `IFRS`, `USGAAP`) para paralelismo normativo configurable.
- **Aprovisionamiento con reversa automática** en `AccountingEngine` para soportar devengación (NIF A-2) sin CFDI en corte.
- **Asiento automático de impuesto diferido** (`TaxEngineMX.build_deferred_tax_policy_lines`) para diferencias temporales (NIF D-4 / IAS 12).
- **Hard close con llave hash** en `mx.close.period` y método de reapertura con validación de clave.
- **Ghost transaction detector** en `account.move` para localizar pólizas LOCAL posteadas sin UUID y no marcadas como accrual/reclass.


## Cockpit UI MVP (Streamlit)

Se añadió un prototipo de interfaz web para conciliación/cumplimiento:

- `scripts/streamlit_financial_cockpit.py`

Ejecución:

```bash
streamlit run scripts/streamlit_financial_cockpit.py
```

Este MVP presenta métricas de integridad, alertas de cierre y conciliación contable-fiscal en una vista tipo dashboard.
