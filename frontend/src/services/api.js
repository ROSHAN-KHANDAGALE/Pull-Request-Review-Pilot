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
