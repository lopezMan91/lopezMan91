# Auditoría técnica rápida (depuración + optimización)

## 1) Detección de bugs y riesgos encontrados

- **Riesgo de inconsistencia de dimensiones**: coexistían referencias a catálogo legacy y catálogo normalizado para profit/cost center.
  - **Mitigación aplicada**: unificación sobre `mx.dimension.value` y validaciones de tipo por dimensión.
- **Riesgo de path traversal lógico en parser XLSX**: el `Target` de workbook relationships podía aceptar rutas fuera de `worksheets/`.
  - **Mitigación aplicada**: validación estricta de `Target` (sin `..`, sin rutas absolutas y prefijo `worksheets/`).
- **Potencial memory growth en importador**: caché de idempotencia sin límite en procesos de larga vida.
  - **Mitigación aplicada**: caché acotado (`OrderedDict`) con política FIFO.

## 2) Gestión de memoria (memory leaks / variables globales)

- No se detectaron *globals* mutables peligrosos para estado compartido.
- Se identificó crecimiento no acotado en caché de idempotencia del importador.
  - **Cambio**: caché con tamaño máximo configurable.
- Se redujo memoria pico en posteo de pólizas al evitar materializar listas duplicadas en `import_and_post_policies`.

## 3) Concurrencia y paralelismo

### ¿Conviene async/threads?
- Para este proyecto, la parte más intensiva observada es **parsing/validación masiva de archivos**.
- Se implementó **multithreading opcional** para parseo (`parse_workers`) con `ThreadPoolExecutor`.
- Para procesos I/O-bound de integración externa (SAT/PAC/APIs), sí convendría `async/await`; en esta base aún no hay cliente asíncrono consolidado.

### Implementación aplicada
- `JournalTemplateImporter(parse_workers=N)` permite fan-out de parseo y validación de filas.
- Script de estrés incluido para comparar `1 worker` vs `4 workers`.

## 4) Pruebas de estrés

Se agregó script:

- `scripts/stress_test_journal_import.py`

Ejemplo:

```bash
python scripts/stress_test_journal_import.py --entries 50000
```

Este script:
- genera CSV masivo,
- ejecuta importación secuencial y paralela,
- mide tiempos y factor de mejora.

## 5) Seguridad

Revisión puntual:
- No se observó inyección SQL directa (uso ORM y utilidades Python en módulos revisados).
- No se detectó exposición de llaves API hardcodeadas en los archivos tocados.
- Endurecimiento aplicado al parser XLSX para evitar rutas de hoja maliciosas.

## 6) Optimización de tiempo de ejecución

Cambios aplicados:
- Validación de locks en lote para evitar patrón N+1 al postear múltiples pólizas.
- Parseo concurrente opcional en importador masivo.
- Menor materialización intermedia en flujo de importación y posteo de pólizas.

