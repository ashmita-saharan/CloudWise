import { useState } from 'react';
import { compareSimulations, runSimulation } from '../services/api';
import ScenarioForm, { defaultScenario } from '../components/ScenarioForm';
import SummaryCards from '../components/SummaryCards';
import VMMetricsTable from '../components/VMMetricsTable';
import TaskTable from '../components/TaskTable';
import ComparisonChart from '../charts/ComparisonChart';
import { downloadJson } from '../services/download';

export default function Dashboard() {
  const [config, setConfig] = useState(defaultScenario);
  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (compare = false) => {
    setBusy(true);
    setError('');
    try {
      if (compare) {
        const data = await compareSimulations(config);
        setComparison(data);
        setResult(data.results[config.algorithm]);
      } else {
        const data = await runSimulation(config);
        setResult(data);
        setComparison(null);
      }
    } catch (problem) {
      setError(problem.message || 'Simulation failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">CloudWise</h1>
            <p className="text-sm text-slate-500">Intelligent resource allocation · SimPy discrete-event simulator</p>
          </div>
          <span className="hidden rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 sm:inline">Local simulation only</span>
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 px-5 py-8">
        <ScenarioForm config={config} setConfig={setConfig} busy={busy}
          onRun={() => submit(false)} onCompare={() => submit(true)} />
        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
        {comparison && <>
          <div className="flex justify-end">
            <button type="button" className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
              onClick={() => downloadJson(comparison, `${comparison.scenario.name}-comparison.json`)}>
              Export comparison JSON
            </button>
          </div>
          <ComparisonChart comparison={comparison} />
        </>}
        {result ? <>
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h2 className="text-xl font-semibold">Results · {result.algorithm}</h2>
              <p className="text-sm text-slate-500">Run ID: {result.runId} · Schema {result.schemaVersion}</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-xs text-slate-500">All time values are simulated seconds</p>
              <button type="button" className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50"
                onClick={() => downloadJson(result, `${result.runId}.json`)}>
                Export run JSON
              </button>
            </div>
          </div>
          <SummaryCards summary={result.summary} />
          <VMMetricsTable rows={result.vmMetrics} />
          <TaskTable rows={result.taskResults} />
        </> : <div className="card p-10 text-center text-slate-500">
          Configure a scenario and run the simulator to see measured model results.
        </div>}
        <p className="pb-6 text-center text-xs text-slate-500">AWLB is a configurable weighted heuristic, not a trained ML model. No real cloud resources are provisioned.</p>
      </main>
    </div>
  );
}
