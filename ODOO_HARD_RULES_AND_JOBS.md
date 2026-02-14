# Reglas duras, jobs y reportes mínimos (MVP)

## Reglas duras (constraints)

1. **Inmutabilidad de evento**
   - `mx.accounting.event` en estado `validated/posted/locked` no permite cambios de campos fuente.
   - Cambios funcionales se manejan por revisión (`revision_of_id`).

2. **Cierre y lock**
   - Periodo bloqueado (`mx.close.period`) impide posteo/import/revaluación para el periodo.
   - Reapertura requiere registro en `mx.close.reopen.log` con solicitante, aprobador y motivo.

3. **Idempotencia de importaciones**
   - `mx.journal.import.batch.import_uid` + `file_hash` se usa como llave de control para reprocesos.

4. **Trazabilidad obligatoria**
   - `account.move`/`line` deben portar `mx_ledger_id` y `mx_event_id` en operaciones automáticas.
   - UUID estructurado (`mx_uuid`) y evidencia (`mx_evidence_url`) para operaciones SAT-relevantes.

## Jobs de cierre (Close Cockpit)

### Diario
- Integridad de datos: eventos sin póliza, pólizas sin evento, UUID duplicado.
- CCM: ajustes manuales de alto riesgo y conflictos SoD.

### Mensual
- Freeze de tasas FX (`mx.rate.table.locked_period`).
- Corrida de revaluación (`mx.fx.revaluation.run`).
- Corridas IFRS16 (posteo mensual de arrendamientos).
- Corridas SAT (`mx.sat.export.run`) para CE y DIOT.
- Publicación de paquete de estados (`mx.statement.package`).

## Reportes mínimos por módulo

- Core: Trial balance por ledger, mayor con drill-down a evento.
- SAT: monitor CFDI vs pólizas, bitácora de exportaciones CE/DIOT.
- FX: exposición por moneda/partner/cuenta + realizado/no realizado.
- IFRS16: roll-forward de pasivo + maturity.
- IFRS9: efectividad de cobertura + OCI/P&L.
- Consolidación: puente sumas → eliminaciones → ajustes → total.
