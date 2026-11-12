function format(value, decimals = 2) {
  return typeof value === 'number' ? value.toFixed(decimals) : '—';
}

export default function SummaryCards({ summary }) {
  const entries = [
    ['Completed', summary.completedTasks, 'tasks'],
    ['Failed', summary.failedTasks, 'tasks'],
    ['Average wait', format(summary.averageWaitingTime), 'simulated s'],
    ['Avg. turnaround', format(summary.averageTurnaroundTime), 'simulated s'],
    ['Throughput', format(summary.throughput, 3), 'tasks / simulated s'],
    ['CPU utilisation', format(summary.averageCpuUtilization * 100, 1), '% modelled'],
    ['RAM utilisation', format(summary.averageRamUtilization * 100, 1), '% modelled'],
    ['Observation time', format(summary.observationTime), 'simulated s'],
  ];
  return (
    <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {entries.map(([label, value, unit]) => (
        <div className="card p-4" key={label}>
          <p className="card-title">{label}</p>
          <p className="mt-2 text-2xl font-bold tabular-nums">{value}</p>
          <p className="mt-1 text-xs text-slate-500">{unit}</p>
        </div>
      ))}
    </section>
  );
}
