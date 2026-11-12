const pretty = (value) => typeof value === 'number' ? value.toFixed(2) : '—';

export default function TaskTable({ rows }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-slate-100 p-5">
        <h3 className="text-base font-semibold">Task results</h3>
        <p className="mt-1 text-xs text-slate-500">First 20 of {rows.length} tasks. Full task data is in the API response or CLI CSV export.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="table-head"><tr>
            {['Task', 'VM', 'Status', 'Arrival (s)', 'Start (s)', 'Finish (s)', 'Wait (s)'].map((head) =>
              <th key={head} className="whitespace-nowrap px-4 py-3">{head}</th>)}
          </tr></thead>
          <tbody>{rows.slice(0, 20).map((task) => <tr key={task.taskId} className="border-t border-slate-100">
            <td className="px-4 py-3 font-medium">{task.taskId}</td>
            <td className="px-4 py-3">{task.assignedVmId || '—'}</td>
            <td className="px-4 py-3">{task.status}</td>
            <td className="px-4 py-3 tabular-nums">{pretty(task.arrivalTime)}</td>
            <td className="px-4 py-3 tabular-nums">{pretty(task.startTime)}</td>
            <td className="px-4 py-3 tabular-nums">{pretty(task.finishTime)}</td>
            <td className="px-4 py-3 tabular-nums">{pretty(task.waitingTime)}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
