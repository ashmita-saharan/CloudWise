import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ComparisonChart({ comparison }) {
  const data = Object.entries(comparison.results).map(([algorithm, result]) => ({
    algorithm,
    'Wait (s)': Number(result.summary.averageWaitingTime.toFixed(3)),
    'Turnaround (s)': Number(result.summary.averageTurnaroundTime.toFixed(3)),
    'Throughput (tasks/s)': Number(result.summary.throughput.toFixed(3)),
  }));
  return (
    <div className="card p-5">
      <h3 className="text-base font-semibold">Algorithm comparison</h3>
      <p className="mt-1 text-xs text-slate-500">Identical hosts, VMs, seeded task lengths and arrival times. Lower wait/turnaround is generally better.</p>
      <div className="mt-5 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 8, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="algorithm" />
            <YAxis width={48} />
            <Tooltip />
            <Legend />
            <Bar dataKey="Wait (s)" fill="#2563eb" />
            <Bar dataKey="Turnaround (s)" fill="#0f766e" />
            <Bar dataKey="Throughput (tasks/s)" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-xs text-slate-500">The combined chart uses different units. Compare values within each metric, not across metric series.</p>
    </div>
  );
}
