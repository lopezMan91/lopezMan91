# Mapa de menús y pantallas (por roles + grupos Odoo)

## AP/AR Clerk (`mx_finance_core.group_mx_ap_ar`)
- **Contabilidad Core / Eventos contables**: captura y seguimiento de eventos.
- **Contabilidad Core / Pólizas en staging**: carga inicial de pólizas importadas.
- **SAT MX / CFDI Vault**: consulta UUID y estatus SAT.

## Contador Local (`mx_finance_core.group_mx_accounting_local`)
- **Contabilidad Core / Inicio**: estado de cierre y alertas.
- **Contabilidad Core / Posting Runs**: validación de corridas event→posting.
- **Contabilidad Core / Pólizas**: validación/posteo/reversa.
- **Control Interno / Period Locks**: operación de cierres.

## Tesorería FX (`mx_finance_core.group_mx_treasury_fx`)
- **Tesorería/FX / Tipos de cambio**: tasas, fuente, freeze por periodo.
- **Tesorería/FX / Revaluación**: preview y posteo por periodo.

## IFRS Specialist (`mx_finance_core.group_mx_accounting_ifrs`)
- **IFRS16**: contratos, tasas, calendarios y reportes.
- **IFRS9**: instrumentos, valuación, coberturas y reportes.
- **Reportes / Diseñador de estados**: taxonomía por norma.
- **IFRS18**: taxonomía y MPM.

## Consolidation Manager (`mx_finance_core.group_mx_consolidation_manager`)
- **Consolidación / Grupo**: perímetro y métodos.
- **Consolidación / Packs**: carga TB y validaciones.
- **Consolidación / Conversión y CTA**: translation runs.
- **Consolidación / Eliminaciones**: matching, top-side, run.

## Policy Admin (`mx_finance_core.group_mx_policy_admin`)
- **Contabilidad Core / Catálogos / Motor de reglas**: versionado, vigencias, aprobaciones.

## Auditor Read Only (`mx_finance_core.group_mx_auditor`)
- **Control Interno / Auditoría**
- **SAT MX / CFDI Vault**
- **Contabilidad Core / Posting Runs**
- **Reportes / Estados**
