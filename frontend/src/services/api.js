import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});

export const submitReview = async (prUrl, includeBenchmark = false) => {
  const { data } = await api.post("/reviews/", {
    pr_url: prUrl,
    include_benchmark: includeBenchmark,
  });
  return data;
};

export const getReview = async (reviewId) => {
  const { data } = await api.get(`/reviews/${reviewId}`);
  return data;
};

export const pollReview = (reviewId, onUpdate, onComplete, onError) => {
  const INTERVAL = 3000; // poll every 3 seconds
  const MAX_ATTEMPTS = 60; // give up after 3 minutes (60 × 3s)
  let attempts = 0;

  const interval = setInterval(async () => {
    attempts++;
    try {
      const data = await getReview(reviewId);
      onUpdate(data);

      if (data.status === "completed" || data.status === "failed") {
        clearInterval(interval);
        onComplete(data);
      }

      if (attempts >= MAX_ATTEMPTS) {
        clearInterval(interval);
        onError(new Error("Review timed out. Please try again."));
      }
    } catch (err) {
      clearInterval(interval);
      onError(err);
    }
  }, INTERVAL);

  // Return cleanup function
  return () => clearInterval(interval);
};