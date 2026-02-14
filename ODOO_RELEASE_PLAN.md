# Odoo Release Plan (MVP -> V1 -> V2)

## Release 1 — MVP (Contabilidad real + SAT base)

### Scope funcional
- Event -> policy -> posting multi-ledger (LOCAL/IFRS).
- Cierre por periodo/ledger con bloqueo y bitácora de reapertura.
- UUID estructurado en asientos (`account.move` y `account.move.line`).
- Export SAT base: catálogo/balanza/pólizas/DIOT por corridas auditables.
- Estados por ledger con drilldown a evento/UUID.
- Importador pólizas con staging y validaciones.

### DoD MVP
- Trazabilidad reporte -> cuenta -> póliza -> evento -> UUID.
- Cierres reproducibles por versión de regla + lock de tasa.
- XML/exports SAT base generables desde el sistema.

## Release 2 — V1 (Enterprise México + IFRS16 + Profit Center)

### Scope funcional
- IFRS16/NIF D-5 completo (contrato, schedule, modificaciones, rollforwards).
- Profit center/cost center/segment/project con allocation engine.
- FX roll-forward por documento (realizado/no realizado).
- SAT full set Anexo 24 + DIOT operacional.
- Close cockpit auditable con evidencia por corrida.

### DoD V1
- Lease engine automático con asientos por ledger y re-medición.
- Reporte FX por documento con TC histórico/cierre.
- Asignaciones por drivers con trazabilidad.

## Release 3 — V2 (Consolidación + IFRS9 Hedge + IFRS18 layer)

### Scope funcional
- Consolidación de grupo con conversiones IAS21, eliminaciones, top-side.
- Hedge accounting IFRS9/NIF C-10 (designación, efectividad, OCI/recycling).
- IFRS18 taxonomy layer + MPM module para presentación corporativa.
- Dashboard intercompany mismatch y reconciliation center.

### DoD V2
- Consolidated FS con bridge de eliminaciones y CTA auditable.
- Hedge docs/effectiveness/postings con historial completo.
- FS builder versionado IFRS18-ready.

## Addons propuestos por paquete
- `account_core_event_engine`
- `account_multi_ledger_mx`
- `l10n_mx_sat_compliance`
- `account_fx_revaluation_pro`
- `account_fs_builder`
- `account_ifrs16_leases`
- `account_profit_center_allocations`
- `account_consolidation_group`
- `account_ifrs9_hedge_accounting`
- `account_ifrs18_reporting_layer`
