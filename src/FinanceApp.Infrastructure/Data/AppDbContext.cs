using Microsoft.EntityFrameworkCore;
using FinanceApp.Domain.Models;

namespace FinanceApp.Infrastructure.Data
{
    public class AppDbContext : DbContext
    {
        public DbSet<Transaction> Transactions => Set<Transaction>();
        public DbSet<Budget> Budgets => Set<Budget>();
        public DbSet<Category> Categories => Set<Category>();

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            optionsBuilder.UseSqlite("Data Source=finance.db");
        }
    }
}
