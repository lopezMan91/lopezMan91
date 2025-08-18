using FinanceApp.Domain.Models;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using System.Text;

namespace FinanceApp.Application.Services
{
    public class ExportService
    {
        public void ToCsv(IEnumerable<Transaction> transactions, string path)
        {
            var sb = new StringBuilder();
            sb.AppendLine("Fecha,Descripcion,Monto,Tipo,Banco,Categoria");
            foreach (var t in transactions)
            {
                sb.AppendLine($"{t.Date:yyyy-MM-dd},{t.Description},{t.Amount},{t.Type},{t.Bank},{t.Category}");
            }
            File.WriteAllText(path, sb.ToString());
        }

        public void ToPdf(IEnumerable<Transaction> transactions, string path)
        {
            Document.Create(container =>
            {
                container.Page(page =>
                {
                    page.Margin(20);
                    page.Content().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.ConstantColumn(80);
                            columns.RelativeColumn();
                            columns.ConstantColumn(80);
                            columns.ConstantColumn(80);
                            columns.RelativeColumn();
                        });
                        table.Header(header =>
                        {
                            header.Cell().Text("Fecha");
                            header.Cell().Text("Descripción");
                            header.Cell().Text("Monto");
                            header.Cell().Text("Tipo");
                            header.Cell().Text("Categoría");
                        });
                        foreach (var t in transactions)
                        {
                            table.Cell().Text(t.Date.ToString("yyyy-MM-dd"));
                            table.Cell().Text(t.Description);
                            table.Cell().Text(t.Amount.ToString());
                            table.Cell().Text(t.Type.ToString());
                            table.Cell().Text(t.Category);
                        }
                    });
                });
            }).GeneratePdf(path);
        }
    }
}
