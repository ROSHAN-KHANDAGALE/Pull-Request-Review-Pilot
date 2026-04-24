import { useState } from "react";
import ReviewForm from "./components/ReviewForm";
import ScoreGauge from "./components/ScoreGauge";
import IssueList from "./components/IssueList";
import BenchmarkPanel from "./components/BenchmarkPanel";
import { submitReview } from "./services/api";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (prUrl, includeBenchmark) => {
    setLoading(true);
    setError("");
    setReview(null);
    try {
      const data = await submitReview(prUrl, includeBenchmark);
      setReview(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo-mark">RP</div>
          <div>
            <h1 className="app-title">ReviewPilot</h1>
            <p className="app-subtitle">AI-native code review agent</p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <ReviewForm onSubmit={handleSubmit} loading={loading} />

        {error && <div className="error-banner">{error}</div>}

        {loading && (
          <div className="loading-state">
            <div className="loading-ring" />
            <p>Fetching diff and running analysis...</p>
          </div>
        )}

        {review && (
          <div className="results-grid">
            <div className="results-top">
              <ScoreGauge score={review.total_score ?? 0} />
              <div className="review-meta">
                <span className="meta-status" data-status={review.status}>
                  {review.status}
                </span>
                <span className="meta-url">{review.pr_url}</span>
                <span className="meta-time">
                  {new Date(review.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            <IssueList issues={review.issues} />
            <BenchmarkPanel benchmark={review.benchmark} />
          </div>
        )}
      </main>
    </div>
  );
}
