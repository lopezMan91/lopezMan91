# Modelo de datos mínimo (Odoo) + 2 flujos end-to-end

## 1) Modelo de datos mínimo

### Ledger y motor
- `mx.finance.ledger`
  - `code`, `principle`, `company_id`
- `mx.accounting.event`
  - `source_model`, `source_id`, `event_type`, `company_id`, `currency_id`, `immutable_hash`, `state`
- `mx.posting.run`
  - `event_id`, `ledger_id`, `rule_version`, `run_at`, `move_ids`, `state`, `log`

### Fiscal (SAT)
- `mx.fiscal.document`
  - `uuid`, `rfc_emisor`, `rfc_receptor`, `total`, `xml_file`, `xml_hash`, `sat_status`, `event_id`, `move_id`

### FX
- `mx.rate.table`
  - `rate_type`, `currency_id`, `company_id`, `rate`, `source`, `loaded_at`, `locked_period`

### Estados financieros
- `mx.reporting.template`
  - `ledger_id`, `statement_type`, `version`, `line_ids`
- `mx.reporting.template.line`
  - `account_prefix`, `sign`, `sequence`

### Grupo / consolidación
- `mx.group.entity`
  - `company_id`, `parent_id`, `ownership_pct`, `control_pct`, `consolidation_method`, `functional_currency_id`, `group_currency_id`

### Arrendamientos IFRS16/NIF D-5
- `mx.lease.contract`
  - `company_id`, `counterparty`, `asset_class`, `commencement_date`, `end_date`, `rate_type`, `annual_rate`, `currency_id`
- `mx.lease.payment`
  - `contract_id`, `payment_date`, `amount`, `variable_flag`

### Importador de pólizas
- `mx.journal.import.batch`
  - `import_uid`, `company_id`, `ledger_id`, `file_hash`, `file_binary`, `preview_json`, `error_log`, `state`, `posting_run_id`

## 2) Flujo end-to-end A (México): Compra con CFDI + pago + salida CE/DIOT

1. Compras crea `account.move` proveedor y dispara `mx.accounting.event` (`supplier_invoice`).
2. Motor contable crea `mx.posting.run` para ledger LOCAL e IFRS.
3. CFDI XML se ingesta en `mx.fiscal.document` y se liga a evento/póliza.
4. Tesorería registra pago, dispara evento `supplier_payment` y posting run.
5. Gates de cierre validan:
   - UUID presente y vigente
   - póliza balanceada
   - periodo no bloqueado
6. Exportadores CE/DIOT usan `account.move` + metadata fiscal para generar salidas.

## 3) Flujo end-to-end B (Grupo): TB IFRS + conversión + eliminación AR/AP + consolidado

1. Filiales entregan TB (ledger IFRS).
2. Se carga estructura de grupo en `mx.group.entity` con % control.
3. Se toman tasas de `mx.rate.table` y se convierte a moneda grupo.
4. Reglas de eliminación generan posting runs en ledger `ELIM` (AR/AP intercompany).
5. Ledger `CONSOL` agrega saldos post-eliminación.
6. Plantillas `mx.reporting.template` emiten Balance/P&L consolidado con drilldown:
   - Consolidado -> entidad -> cuenta -> póliza -> evento -> UUID.

## 4) Extensiones implementadas en esta iteración (audit-ready)

- `mx.accounting.policy` + `mx.accounting.policy.version` para reglas versionadas (policy-as-code).
- `mx.close.period` + `mx.close.reopen.log` para gobierno de cierre y bitácora de reaperturas.
- `mx.dimension` + `mx.account.rule` para profit/cost center y controles de cuenta obligatorios.
- `mx.intercompany.tag` para matching y trazabilidad de eliminaciones intercompany.
- `mx.hedge.instrument` para inventario de coberturas IFRS 9 / NIF C-10.
- `mx.statement.package` para publicación controlada de estados financieros.
- `mx.journal.import.line` para staging de líneas con validaciones contables fuertes.
- `account.move` / `account.move.line` extendidos con: `mx_ledger_id`, `mx_event_id`, `mx_uuid`, `mx_evidence_url`.
- `mx.sat.export.run` para corridas SAT (catálogo/balanza/pólizas/DIOT) con checksum y log.
- `mx.close.cockpit` + `mx.close.cockpit.item` para checklist auditable de corridas de cierre.
