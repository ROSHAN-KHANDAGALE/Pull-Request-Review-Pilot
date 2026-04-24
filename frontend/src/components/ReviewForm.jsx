import { useState } from "react";

export default function ReviewForm({ onSubmit, loading }) {
  const [prUrl, setPrUrl] = useState("");
  const [includeBenchmark, setIncludeBenchmark] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = () => {
    if (!prUrl.startsWith("https://github.com/")) {
      setError("URL must start with https://github.com/");
      return;
    }
    setError("");
    onSubmit(prUrl, includeBenchmark);
  };

  return (
    <div className="form-card">
      <div className="form-header">
        <span className="form-label">PULL REQUEST URL</span>
      </div>
      <div className="input-row">
        <input
          type="text"
          className="pr-input"
          placeholder="https://github.com/owner/repo/pull/123"
          value={prUrl}
          onChange={(e) => setPrUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          disabled={loading}
        />
        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? <span className="spinner" /> : "Analyze"}
        </button>
      </div>
      {error && <p className="input-error">{error}</p>}
      <label className="benchmark-toggle">
        <input
          type="checkbox"
          checked={includeBenchmark}
          onChange={(e) => setIncludeBenchmark(e.target.checked)}
          disabled={loading}
        />
        <span>Include benchmark comparison</span>
      </label>
    </div>
  );
}
