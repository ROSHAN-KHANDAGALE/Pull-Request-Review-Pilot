export default function BenchmarkPanel({ benchmark }) {
  if (!benchmark) return null;

  const {
    agent_score,
    baseline_score,
    agent_issue_count,
    baseline_issue_count,
  } = benchmark;
  const diff = agent_score - baseline_score;
  const diffLabel = diff >= 0 ? `+${diff}` : `${diff}`;
  const agentPct = Math.round((agent_score / 10000) * 100);
  const basePct = Math.round((baseline_score / 10000) * 100);

  return (
    <div className="benchmark-panel">
      <div className="section-header">
        <span>Benchmark Comparison</span>
        <span
          className="diff-badge"
          style={{
            color: diff >= 0 ? "var(--score-high)" : "var(--score-low)",
          }}
        >
          {diffLabel} pts
        </span>
      </div>

      <div className="bench-row">
        <div className="bench-col">
          <span className="bench-label">ReviewPilot Agent</span>
          <div className="bench-bar-track">
            <div
              className="bench-bar agent"
              style={{ width: `${agentPct}%` }}
            />
          </div>
          <span className="bench-score">{agent_score.toLocaleString()}</span>
          <span className="bench-issues">{agent_issue_count} issues found</span>
        </div>

        <div className="bench-col">
          <span className="bench-label">Vanilla Claude</span>
          <div className="bench-bar-track">
            <div
              className="bench-bar baseline"
              style={{ width: `${basePct}%` }}
            />
          </div>
          <span className="bench-score">{baseline_score.toLocaleString()}</span>
          <span className="bench-issues">
            {baseline_issue_count} issues found
          </span>
        </div>
      </div>

      <p className="bench-note">
        Agent uses category-weighted scoring (correctness 4000pts, security
        2000pts). Baseline uses flat severity deductions — no category
        awareness.
      </p>
    </div>
  );
}
