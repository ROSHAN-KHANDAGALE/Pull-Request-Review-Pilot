import { useState, useEffect, useRef } from "react";
import ReviewForm from "./components/ReviewForm";
import ScoreGauge from "./components/ScoreGauge";
import IssueList from "./components/IssueList";
import BenchmarkPanel from "./components/BenchmarkPanel";
import { submitReview, pollReview } from "./services/api";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const cleanupRef = useRef(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) cleanupRef.current();
    };
  }, []);

  const handleSubmit = async (prUrl, includeBenchmark) => {
    // Cancel any existing poll
    if (cleanupRef.current) cleanupRef.current();

    setLoading(true);
    setError("");
    setReview(null);
    setStatus("pending");

    try {
      // Step 1 — submit, get review id back instantly
      const initial = await submitReview(prUrl, includeBenchmark);
      setReview(initial);
      setStatus(initial.status);

      // Step 2 — start polling
      cleanupRef.current = pollReview(
        initial.id,
        // onUpdate — called every poll tick
        (data) => {
          setReview(data);
          setStatus(data.status);
        },
        // onComplete — called when status is completed or failed
        (data) => {
          setReview(data);
          setStatus(data.status);
          setAttempts(prev => prev + 1);
        },
        // onError — called on network error or timeout
        (err) => {
          setError(err.message || "Something went wrong.");
          setLoading(false);
        },
      );
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit review.");
      setLoading(false);
    }
  };

  const getStatusMessage = () => {
  switch (status) {
    case 'pending':    return `Queued — waiting for worker... (${attempts}s)`;
    case 'processing': return `Running analysis... (${attempts * 3}s elapsed)`;
    default:           return null;
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

        {/* Status indicator while loading */}
        {loading && (
          <div className="loading-state">
            <div className="loading-ring" />
            <p>{getStatusMessage()}</p>
          </div>
        )}

        {/* Failed state */}
        {!loading && status === "failed" && (
          <div className="error-banner">
            Review failed. The diff may be too large or the GitHub URL may be
            invalid.
          </div>
        )}

        {/* Results */}
        {!loading && review && status === "completed" && (
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
};