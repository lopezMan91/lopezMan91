using FinanceApp.Domain.Models;
using FinanceApp.Infrastructure.Data;

namespace FinanceApp.Infrastructure.Repositories
{
    public class TransactionRepository
    {
        private readonly AppDbContext _ctx;
        public TransactionRepository(AppDbContext ctx)
        {
            _ctx = ctx;
        }

        public void AddRange(IEnumerable<Transaction> transactions)
        {
            _ctx.Transactions.AddRange(transactions);
            _ctx.SaveChanges();
        }

        public IEnumerable<Transaction> GetAll() => _ctx.Transactions.ToList();
    }
}
