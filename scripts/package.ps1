param(
    [string]$Runtime = "win-x64"
)

$publishDir = "dist/publish"
dotnet publish src/FinanceApp.UI/FinanceApp.UI.csproj -c Release -r $Runtime --self-contained true -p:PublishSingleFile=true -o $publishDir

$exe = Join-Path $publishDir "FinanceApp.UI.exe"
# Requiere que squirrel esté instalado y en el PATH
squirrel --releasify $exe --releaseDir dist
