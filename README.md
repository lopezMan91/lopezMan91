# FinanceApp

Aplicación de escritorio para Windows 11 que permite importar transacciones desde PDFs de estados de cuenta, clasificarlas y gestionar presupuestos.

## Estructura
- `FinanceApp.sln` - Solución principal.
- `src/` - Código fuente dividido en capas (Domain, Infrastructure, Application, UI).
- `tests/` - Pruebas unitarias con xUnit.
- `sample-data/` - PDFs y CSVs de ejemplo.
- `scripts/` - Scripts de build y empaquetado para Windows.

## Requisitos
- Windows 11 con [.NET SDK 8](https://dotnet.microsoft.com/download).
- PowerShell 7.

## Compilación
```powershell
scripts/build.ps1
```
El script ejecuta `dotnet restore`, `dotnet build` y `dotnet test`.

## Empaquetado
Genera ejecutable e instalador Squirrel:
```powershell
scripts/package.ps1
```
Los artefactos se generan en `dist/`.

## Uso rápido
1. Instala el paquete generado.
2. Abre la aplicación *Finanzas*.
3. Importa PDFs desde la pantalla **Importar**.
4. Revisa la clasificación automática y ajusta reglas desde **Clasificación**.
5. Define presupuestos en **Presupuestos** y analiza el **Dashboard**.

## Datos de ejemplo
En `sample-data/pdfs` se incluyen tres PDFs de bancos ficticios. El CSV esperado de cada uno está en `sample-data/expected`.

## Tests
```powershell
# Ejecutar desde la raíz
scripts/build.ps1
```
Valida el importador y la clasificación (objetivo >=95% filas válidas y >=80% precisión).

## Empaquetado manual
Si no usas los scripts, puedes ejecutar:
```powershell
# Build
 dotnet publish src/FinanceApp.UI/FinanceApp.UI.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o dist/publish
# Squirrel (requiere herramientas instaladas)
 squirrel --releasify dist/publish/FinanceApp.UI.exe
```

## Nota
La aplicación funciona completamente offline y almacena datos en SQLite. Revisa `appsettings.json` para toggles como telemetría (desactivada por defecto).
