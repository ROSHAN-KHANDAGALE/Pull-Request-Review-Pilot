import { useState } from "react";

export default function ReviewForm({
  onSubmit,
  loading,
  queueEnabled,
  useQueue,
  onQueueChange,
  rateLimitingEnabled,
}) {
  const [prUrl, setPrUrl] = useState("");
  const [includeBenchmark, setIncludeBenchmark] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = () => {
    if (!prUrl.startsWith("https://github.com/")) {
      setError("URL must start with https://github.com/");
      return;
    }
    setError("");
    onSubmit(prUrl, includeBenchmark, useQueue);
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
      <label className="feature-toggle">
        <input
          type="checkbox"
          checked={useQueue}
          onChange={(e) => onQueueChange(e.target.checked)}
          disabled={loading || !queueEnabled}
        />
        <span>Use background worker (Celery/Redis)</span>
        {!queueEnabled && <span className="feature-note">Disabled by server</span>}
      </label>
      <p className="feature-status">
        API rate limiting: {rateLimitingEnabled ? "on" : "off"} (server controlled)
      </p>
    </div>
  );
}
