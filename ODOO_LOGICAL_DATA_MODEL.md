# Diagrama lógico de datos (resumen)

## Núcleo contable
- `mx.accounting.event` -> `mx.posting.run` -> `account.move`
- `mx.accounting.policy` -> `mx.accounting.policy.version` (vigencias)
- `account.move`/`account.move.line` extendidos con:
  - `mx_ledger_id`, `mx_event_id`, `mx_policy_version_id`, `mx_uuid`, `mx_evidence_url`

## Multi-ledger / empresa
- `res.company` 1..n `mx.finance.ledger`
- `mx.close.period` + `mx.close.reopen.log`

## SAT
- `mx.fiscal.document` (UUID + XML + estatus)
- `mx.sat.export.run` (catálogo/balanza/pólizas/auxiliares/DIOT)

## FX
- `mx.rate.table` (spot/promedio/cierre/histórico + lock)

## Dimensiones y allocations
- `mx.dimension`, `mx.account.rule`

## IFRS 16
- `mx.lease.contract` -> `mx.lease.payment`

## IFRS 9
- `mx.hedge.instrument`

## Estados financieros
- `mx.reporting.template` -> `mx.reporting.template.line`
- `mx.statement.package`

## Consolidación
- `mx.group.entity`
- `mx.intercompany.tag` (matching/eliminación)

## Control interno
- `mx.close.cockpit` -> `mx.close.cockpit.item`
