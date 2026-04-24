const SEVERITY_META = {
  critical: { color: "var(--sev-critical)", dot: "●" },
  major: { color: "var(--sev-major)", dot: "●" },
  minor: { color: "var(--sev-minor)", dot: "●" },
  info: { color: "var(--sev-info)", dot: "●" },
};

const CATEGORY_LABEL = {
  correctness: "Correctness",
  security: "Security",
  maintainability: "Maintainability",
  test_coverage: "Test Coverage",
  documentation: "Documentation",
};

export default function IssueList({ issues }) {
  if (!issues?.length) {
    return <div className="no-issues">No issues found — clean diff ✓</div>;
  }

  const order = ["critical", "major", "minor", "info"];
  const sorted = [...issues].sort(
    (a, b) => order.indexOf(a.severity) - order.indexOf(b.severity),
  );

  return (
    <div className="issue-list">
      <div className="section-header">
        <span>Issues</span>
        <span className="issue-count">{issues.length}</span>
      </div>
      {sorted.map((issue) => {
        const meta = SEVERITY_META[issue.severity] || SEVERITY_META.info;
        return (
          <div key={issue.id} className="issue-card">
            <div className="issue-top">
              <span className="issue-dot" style={{ color: meta.color }}>
                {meta.dot}
              </span>
              <span className="issue-severity" style={{ color: meta.color }}>
                {issue.severity.toUpperCase()}
              </span>
              <span className="issue-category">
                {CATEGORY_LABEL[issue.category] || issue.category}
              </span>
              {issue.file_path && (
                <span className="issue-file">
                  {issue.file_path}
                  {issue.line_number ? `:${issue.line_number}` : ""}
                </span>
              )}
            </div>
            <p className="issue-title">{issue.title}</p>
            <p className="issue-desc">{issue.description}</p>
            {issue.suggestion && (
              <div className="issue-suggestion">
                <span className="suggestion-label">Suggestion</span>
                <p>{issue.suggestion}</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
