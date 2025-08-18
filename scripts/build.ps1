dotnet restore
dotnet build FinanceApp.sln -c Release
dotnet test tests/FinanceApp.Tests/FinanceApp.Tests.csproj -c Release
