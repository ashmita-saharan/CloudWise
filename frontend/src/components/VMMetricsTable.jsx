export default function VMMetricsTable({ rows }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-slate-100 p-5">
        <h3 className="text-base font-semibold">Virtual machine metrics</h3>
        <p className="mt-1 text-xs text-slate-500">CPU/RAM percentages use simulated resource-time accounting.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="table-head"><tr>
            {['VM', 'Host', 'MIPS', 'Assigned', 'Completed', 'CPU util.', 'RAM util.'].map((head) =>
              <th key={head} className="whitespace-nowrap px-4 py-3">{head}</th>)}
          </tr></thead>
          <tbody>{rows.map((vm) => <tr key={vm.vmId} className="border-t border-slate-100">
            <td className="px-4 py-3 font-medium">{vm.vmId}</td>
            <td className="px-4 py-3">{vm.hostId}</td>
            <td className="px-4 py-3 tabular-nums">{vm.totalMips}</td>
            <td className="px-4 py-3 tabular-nums">{vm.assignedTasks}</td>
            <td className="px-4 py-3 tabular-nums">{vm.completedTasks}</td>
            <td className="px-4 py-3 tabular-nums">{(vm.cpuUtilization * 100).toFixed(1)}%</td>
            <td className="px-4 py-3 tabular-nums">{(vm.ramUtilization * 100).toFixed(1)}%</td>
          </tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
