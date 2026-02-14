# Backlog priorizado (Epic → Feature → Story) para Odoo MX Finance Core

## Epic 0 — Foundation (Multi-ledger + Event Engine)

### Feature 0.1 Data model base
- Story: Como arquitecto quiero modelos `BusinessEvent`, `PostingRun`, `Ledger`, `FiscalDocument`, `RateTable`, `ReportingTemplate`, `GroupStructure` para soportar SAT + IFRS + consolidación.
- Criterios de aceptación:
  - Se pueden crear registros por UI/API.
  - Existe trazabilidad `Event -> PostingRun -> account.move`.
  - Existen ledgers seed: LOCAL/IFRS/CONSOL/ELIM.

### Feature 0.2 Policy-as-code versionado
- Story: Como controller quiero versionar reglas contables por norma/entidad/evento para re-ejecutar cierres históricos.
- Criterios:
  - `rule_version` obligatorio por `PostingRun`.
  - Cambio de versión no altera corridas históricas.

## Epic 1 — SAT Compliance (MVP)

### Feature 1.1 Fiscal Vault
- Story: Como fiscalista quiero CFDI first-class con UUID y estatus SAT para evitar cierres con riesgo.
- Criterios:
  - Vínculo obligatorio `UUID <-> póliza <-> evento`.
  - Gate de cierre falla con CFDI cancelado/no encontrado.

### Feature 1.2 Contabilidad Electrónica (Anexo 24)
- Story: Como contabilidad quiero generar XML de catálogo/balanza/pólizas/auxiliares para SAT.
- Criterios:
  - Export por periodo y compañía.
  - Validación previa de esquema y agrupador.

### Feature 1.3 DIOT
- Story: Como impuestos quiero salida DIOT desde AP/GL sin Excel.
- Criterios:
  - Export por periodo/proveedor.
  - Bitácora de presentación.

## Epic 2 — Financial Statement Builder

### Feature 2.1 Templates versionados
- Story: Como Finanzas quiero plantillas Balance/P&L/CF por ledger.
- Criterios:
  - Versiones por norma y vigencia.
  - Drilldown a mayor y póliza.

### Feature 2.2 NIF vs IFRS bridge
- Story: Como corporativo quiero puente NIF↔IFRS por rubro.
- Criterios:
  - Reporte lado a lado por cuenta/rubro.
  - Ajustes IFRS identificables por tema.

## Epic 3 — Consolidación (MVP)

### Feature 3.1 Perímetro y ownership
- Story: Como grupo quiero jerarquía legal con %control y método consolidación.
- Criterios:
  - Árbol de grupo con vigencias.
  - Métodos full/proportional/equity.

### Feature 3.2 Conversión y eliminaciones básicas
- Story: Como consolidación quiero convertir TB a moneda grupo y eliminar intercompany base.
- Criterios:
  - Traducción IAS 21 (BS cierre / P&L promedio).
  - Eliminación AR/AP y ventas/COGS interco.

## Epic 4 — IFRS 16 / NIF D-5 Lease Engine

### Feature 4.1 Captura y medición
- Story: Como contabilidad quiero capturar contrato una vez y generar PV + ROU + schedule.
- Criterios:
  - Hard-stop sin tasa aprobada.
  - Hard-stop sin calendario válido.

### Feature 4.2 Remeasurement + modifications
- Story: Como contabilidad quiero recalcular por índice/plazo/opción y postear delta.
- Criterios:
  - Snapshot de supuestos y evidencia.
  - Asiento delta sin reescribir histórico.

## Epic 5 — Journal Importer (Excel/CSV)

### Feature 5.1 Staging + approval
- Story: Como controller quiero importar pólizas a staging, validar y aprobar antes de postear.
- Criterios:
  - Preview agrupado por póliza.
  - Estado `loaded -> validated -> approved -> posted`.

### Feature 5.2 Validaciones auditor
- Story: Como auditor quiero bloqueos de cuentas, partner, FX, balanceo e idempotencia.
- Criterios:
  - `sum(debit)=sum(credit)` por póliza.
  - Duplicados bloqueados por Import UID.

## Epic 6 — Controls (COSO operativo)

### Feature 6.1 SoD + approvals
- Story: Como control interno quiero SoD y workflow por riesgo/monto.
- Criterios:
  - Roles conflictivos bloqueados.
  - Reapertura de periodo con evidencia y aprobador.

### Feature 6.2 Reconciliations + Close cockpit
- Story: Como cierre quiero checklist y conciliaciones con aging y evidencia.
- Criterios:
  - AP/AR/Bank/Inventory vs GL reconciliables.
  - KPI de cierre y pendientes auditables.
