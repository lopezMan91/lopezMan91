using FinanceApp.Domain.Enums;

namespace FinanceApp.Domain.Models
{
    public class Transaction
    {
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public string Description { get; set; } = string.Empty;
        public decimal Amount { get; set; }
        public TransactionType Type { get; set; }
        public string Category { get; set; } = string.Empty;
        public string Bank { get; set; } = string.Empty;
    }
}
