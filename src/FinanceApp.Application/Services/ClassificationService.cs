using FinanceApp.Domain.Models;
using System.Text.Json;

namespace FinanceApp.Application.Services
{
    public class ClassificationService
    {
        private readonly Dictionary<string,string> _rules = new();
        private readonly Dictionary<(string word,string category), int> _wordCategoryCounts = new();
        private bool _trained;

        private record Rule(string Keyword, string Category);

        public ClassificationService(string? rulePath = null)
        {
            if (rulePath != null && File.Exists(rulePath))
            {
                var json = File.ReadAllText(rulePath);
                var rules = JsonSerializer.Deserialize<List<Rule>>(json);
                if (rules != null)
                    foreach (var r in rules)
                        _rules[r.Keyword.ToLower()] = r.Category;
            }
            else
            {
                _rules["super"] = "Alimentos";
                _rules["restaurante"] = "Comida";
                _rules["nomina"] = "Ingresos";
            }
        }

        public void AddRule(string keyword, string category) => _rules[keyword.ToLower()] = category;

        public string Classify(Transaction tx)
        {
            var lower = tx.Description.ToLower();
            foreach (var rule in _rules)
                if (lower.Contains(rule.Key))
                    return rule.Value;
            return "Sin categoría";
        }

        public void Train(IEnumerable<Transaction> labeled)
        {
            foreach (var tx in labeled)
            {
                var words = tx.Description.ToLower().Split(' ');
                foreach (var w in words)
                {
                    var key = (w, tx.Category);
                    _wordCategoryCounts[key] = _wordCategoryCounts.TryGetValue(key, out var c) ? c + 1 : 1;
                }
            }
            _trained = true;
        }

        public string Predict(Transaction tx)
        {
            if (!_trained) return Classify(tx);
            var scores = new Dictionary<string, int>();
            var words = tx.Description.ToLower().Split(' ');
            foreach (var w in words)
            {
                foreach (var key in _wordCategoryCounts.Keys)
                {
                    if (key.word == w)
                    {
                        if (!scores.ContainsKey(key.category)) scores[key.category] = 0;
                        scores[key.category] += _wordCategoryCounts[key];
                    }
                }
            }
            if (scores.Count == 0) return Classify(tx);
            return scores.OrderByDescending(k => k.Value).First().Key;
        }
    }
}
