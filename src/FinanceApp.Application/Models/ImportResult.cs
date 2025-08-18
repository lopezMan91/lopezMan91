using FinanceApp.Domain.Models;

namespace FinanceApp.Application.Models
{
    public record ImportResult(List<Transaction> Transactions, int ParsedRows, int TotalRows);
}
