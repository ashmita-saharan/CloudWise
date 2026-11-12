const fields = [
  { key: 'hosts', label: 'Hosts', min: 1 },
  { key: 'vms', label: 'Virtual machines', min: 1 },
  { key: 'tasks', label: 'Tasks', min: 0 },
  { key: 'seed', label: 'Random seed' },
  { key: 'arrival_window', label: 'Arrival window (s)', min: 0 },
];

export const defaultScenario = {
  name: 'dashboard', hosts: 3, vms: 6, tasks: 100, seed: 42,
  algorithm: 'AWLB', arrival_window: 30,
};

export default function ScenarioForm({ config, setConfig, busy, onRun, onCompare }) {
  const update = (key, value) => setConfig((current) => ({ ...current, [key]: value }));
  return (
    <form className="card p-5" onSubmit={(event) => { event.preventDefault(); onRun(); }}>
      <h2 className="text-lg font-semibold">Scenario configuration</h2>
      <p className="mt-1 text-sm text-slate-500">Change inputs, then run one algorithm or compare all three on the same workload.</p>
      <div className="mt-5 grid grid-cols-2 gap-4 md:grid-cols-3">
        {fields.map((field) => (
          <label className="text-sm font-medium text-slate-700" key={field.key}>
            {field.label}
            <input
              type="number"
              min={field.min}
              required
              step={field.key === 'arrival_window' ? 'any' : '1'}
              value={config[field.key]}
              onChange={(event) => update(field.key, Number(event.target.value))}
            />
          </label>
        ))}
        <label className="text-sm font-medium text-slate-700">
          VM-selection policy
          <select value={config.algorithm} onChange={(event) => update('algorithm', event.target.value)}>
            <option value="FCFS">FCFS</option>
            <option value="RR">Round Robin</option>
            <option value="AWLB">Adaptive weighted (AWLB)</option>
          </select>
        </label>
      </div>
      <div className="mt-5 flex flex-wrap gap-3">
        <button disabled={busy} type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
          {busy ? 'Running…' : 'Run simulation'}
        </button>
        <button disabled={busy} type="button" onClick={onCompare}
          className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-100">
          Compare FCFS / RR / AWLB
        </button>
      </div>
    </form>
  );
}
