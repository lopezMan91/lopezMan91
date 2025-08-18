using UglyToad.PdfPig;
using FinanceApp.Domain.Models;
using FinanceApp.Domain.Enums;
using FinanceApp.Application.Models;

namespace FinanceApp.Application.Services
{
    public class PdfImportService
    {
        public ImportResult Import(string path, string bank)
        {
            var transactions = new List<Transaction>();
            int total = 0;
            using var document = PdfDocument.Open(path);
            foreach (var page in document.GetPages())
            {
                var lines = page.Text.Split('\n');
                foreach (var line in lines)
                {
                    if (string.IsNullOrWhiteSpace(line) || line.StartsWith("Fecha"))
                        continue;
                    total++;
                    var parts = line.Split(',');
                    if (parts.Length < 4) continue;
                    if (!DateTime.TryParse(parts[0], out var date)) continue;
                    if (!decimal.TryParse(parts[2], out var amount)) continue;
                    var type = parts[3].Contains("Cargo", StringComparison.OrdinalIgnoreCase) ? TransactionType.Debit : TransactionType.Credit;
                    transactions.Add(new Transaction
                    {
                        Date = date,
                        Description = parts[1].Trim(),
                        Amount = amount,
                        Type = type,
                        Bank = bank
                    });
                }
            }
            return new ImportResult(transactions, transactions.Count, total);
        }
    }
}
