import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - clear token and redirect to login
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: { email: string; full_name: string; password: string }) =>
    api.post("/api/v1/auth/register", data),
  
  login: (email: string, password: string) =>
    api.post("/api/v1/auth/login", new URLSearchParams({
      username: email,
      password: password,
    }), {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }),
  
  getMe: () => api.get("/api/v1/auth/me"),
};

// Stations API
export const stationsAPI = {
  list: (query?: string, limit = 100) =>
    api.get("/api/v1/stations", { params: { q: query, limit } }),
  
  autocomplete: (query: string, limit = 10) =>
    api.get("/api/v1/stations/autocomplete", { params: { q: query, limit } }),
  
  get: (code: string) =>
    api.get(`/api/v1/stations/${code}`),
};

// Trains API
export const trainsAPI = {
  list: (limit = 100, offset = 0) =>
    api.get("/api/v1/trains", { params: { limit, offset } }),
  
  get: (number: string) =>
    api.get(`/api/v1/trains/${number}`),
  
  getRoute: (number: string) =>
    api.get(`/api/v1/trains/${number}/route`),
};

// Search API
export const searchAPI = {
  search: (params: {
    from_station: string;
    to_station: string;
    journey_date: string;
    limit?: number;
  }) =>
    api.get("/api/v1/search", { params }),
  
  searchDirect: (from_station: string, to_station: string) =>
    api.get("/api/v1/search/direct", { params: { from_station, to_station } }),
};

// Bookings API
export const bookingsAPI = {
  create: (data: {
    train_run_id: number;
    from_station_code: string;
    to_station_code: string;
    journey_date: string;
    seat_class: string;
    passengers: Array<{
      name: string;
      age: number;
      gender: string;
    }>;
  }) =>
    api.post("/api/v1/bookings", data),
  
  list: () =>
    api.get("/api/v1/bookings"),
  
  get: (bookingId: string) =>
    api.get(`/api/v1/bookings/${bookingId}`),
  
  cancel: (bookingId: string) =>
    api.post(`/api/v1/bookings/${bookingId}/cancel`),
};

export default api;
