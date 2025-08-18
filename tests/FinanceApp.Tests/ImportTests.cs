using Xunit;
using FinanceApp.Application.Services;
using System.IO;

namespace FinanceApp.Tests
{
    public class ImportTests
    {
        [Fact]
        public void ImportPdf_ParsesTransactions()
        {
            var service = new PdfImportService();
            var path = Path.Combine("..", "..", "sample-data", "pdfs", "bank_a.pdf");
            var result = service.Import(path, "BancoA");
            Assert.True(result.Transactions.Count > 0);
            Assert.True(result.ParsedRows >= 0.95 * result.TotalRows);
        }
    }
}
