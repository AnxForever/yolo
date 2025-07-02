import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

export const uploadApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for uploads
  headers: {
    "Content-Type": "multipart/form-data",
  },
});

// Add a response interceptor for logging errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

uploadApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("Upload API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
); 