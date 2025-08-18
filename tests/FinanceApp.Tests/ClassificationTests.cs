using Xunit;
using FinanceApp.Application.Services;
using FinanceApp.Domain.Models;
using System.Collections.Generic;

namespace FinanceApp.Tests
{
    public class ClassificationTests
    {
        [Fact]
        public void RuleEngine_ClassifiesTransactions()
        {
            var service = new ClassificationService();
            var transactions = new List<Transaction>
            {
                new() { Description = "Supermercado A", Category = "Alimentos" },
                new() { Description = "Restaurante B", Category = "Comida" },
                new() { Description = "Nomina", Category = "Ingresos" }
            };
            service.Train(transactions);
            int correct = 0;
            foreach (var tx in transactions)
            {
                var predicted = service.Predict(tx);
                if (predicted == tx.Category) correct++;
            }
            Assert.True(correct >= 0.8 * transactions.Count);
        }
    }
}
