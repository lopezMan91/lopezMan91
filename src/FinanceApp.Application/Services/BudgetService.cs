using FinanceApp.Infrastructure.Data;
using FinanceApp.Domain.Models;

namespace FinanceApp.Application.Services
{
    public class BudgetService
    {
        private readonly AppDbContext _ctx;
        public BudgetService(AppDbContext ctx)
        {
            _ctx = ctx;
        }

        public Budget Create(Budget budget)
        {
            _ctx.Budgets.Add(budget);
            _ctx.SaveChanges();
            return budget;
        }

        public IEnumerable<Budget> GetBudgets() => _ctx.Budgets.ToList();
    }
}
