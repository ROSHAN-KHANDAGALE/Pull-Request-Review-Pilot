import { useState, useEffect, useRef } from "react";
import ReviewForm from "./components/ReviewForm";
import ScoreGauge from "./components/ScoreGauge";
import IssueList from "./components/IssueList";
import BenchmarkPanel from "./components/BenchmarkPanel";
import { getReviewOptions, submitReview, pollReview } from "./services/api";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [options, setOptions] = useState(null);
  const [optionsError, setOptionsError] = useState("");
  const [useQueue, setUseQueue] = useState(false);
  const cleanupRef = useRef(null);

  useEffect(() => {
    let active = true;
    getReviewOptions()
      .then((data) => {
        if (!active) return;
        setOptions(data);
        setUseQueue(data.queue_enabled);
      })
      .catch((err) => {
        if (active) {
          setOptionsError(
            err.response?.data?.detail || "Could not load review settings.",
          );
        }
      });

    return () => {
      active = false;
      if (cleanupRef.current) cleanupRef.current();
    };
  }, []);

  const handleSubmit = async (prUrl, includeBenchmark, shouldUseQueue) => {
    if (cleanupRef.current) cleanupRef.current();

    setLoading(true);
    setError("");
    setReview(null);
    setAttempts(0);
    setStatus(shouldUseQueue ? "pending" : "processing");

    try {
      const executionMode = shouldUseQueue ? "queued" : "direct";
      const initial = await submitReview(prUrl, includeBenchmark, executionMode);
      setReview(initial);
      setStatus(initial.status);

      if (!shouldUseQueue) {
        setLoading(false);
        return;
      }

      cleanupRef.current = pollReview(
        initial.id,
        (data) => {
          setReview(data);
          setStatus(data.status);
          setAttempts((prev) => prev + 1);
        },
        (data) => {
          setReview(data);
          setStatus(data.status);
          setLoading(false);
        },
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
    if (status === "pending") {
      return `Queued — waiting for worker... (${attempts * 3}s elapsed)`;
    }
    if (status === "processing") {
      return useQueue
        ? `Running analysis... (${attempts * 3}s elapsed)`
        : "Running analysis directly...";
    }
    return null;
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
        <ReviewForm
          onSubmit={handleSubmit}
          loading={loading || options === null || Boolean(optionsError)}
          queueEnabled={Boolean(options?.queue_enabled)}
          useQueue={useQueue}
          onQueueChange={setUseQueue}
          rateLimitingEnabled={Boolean(options?.rate_limiting_enabled)}
        />

        {optionsError && <div className="error-banner">{optionsError}</div>}
        {error && <div className="error-banner">{error}</div>}

        {loading && (
          <div className="loading-state">
            <div className="loading-ring" />
            <p>{getStatusMessage()}</p>
          </div>
        )}

        {!loading && status === "failed" && (
          <div className="error-banner">
            Review failed. Check the GitHub PR URL, backend worker logs, and
            that MODEL_NAME is a supported chat-completions model.
          </div>
        )}

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
}
