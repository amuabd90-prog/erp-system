async function loadCharts() {
  const trend = document.getElementById("salesTrendChart");
  if (!trend) return;
  const res = await fetch("/api/charts");
  const data = await res.json();

  new Chart(trend, {
    type: "line",
    data: {
      labels: data.sales_trend.map((x) => x.date),
      datasets: [{ label: "Sales", data: data.sales_trend.map((x) => x.amount) }]
    }
  });
  new Chart(document.getElementById("revenuePieChart"), {
    type: "pie",
    data: {
      labels: data.revenue_by_item.map((x) => x.item),
      datasets: [{ data: data.revenue_by_item.map((x) => x.amount) }]
    }
  });

  const monthKeys = [...new Set(data.monthly_sales.map((x) => x.month).concat(data.monthly_expenses.map((x) => x.month)))];
  const salesMap = Object.fromEntries(data.monthly_sales.map((x) => [x.month, x.amount]));
  const expMap = Object.fromEntries(data.monthly_expenses.map((x) => [x.month, x.amount]));
  new Chart(document.getElementById("monthlyBarChart"), {
    type: "bar",
    data: {
      labels: monthKeys,
      datasets: [
        { label: "Revenue", data: monthKeys.map((m) => salesMap[m] || 0) },
        { label: "Expenses", data: monthKeys.map((m) => expMap[m] || 0) }
      ]
    }
  });
  new Chart(document.getElementById("taxDoughnutChart"), {
    type: "doughnut",
    data: {
      labels: ["VAT", "Profit Tax"],
      datasets: [{ data: [data.tax.vat, data.tax.profit_tax] }]
    }
  });
}

document.addEventListener("DOMContentLoaded", loadCharts);
