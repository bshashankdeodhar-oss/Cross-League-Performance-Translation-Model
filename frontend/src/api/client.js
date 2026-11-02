import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

let inMemoryToken = localStorage.getItem('clptm_token') || null;

export const setAccessToken = (token) => {
  inMemoryToken = token;
  if (token) {
    localStorage.setItem('clptm_token', token);
  } else {
    localStorage.removeItem('clptm_token');
  }
};

export const getAccessToken = () => {
  return inMemoryToken;
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  if (inMemoryToken) {
    config.headers.Authorization = `Bearer ${inMemoryToken}`;
  }
  return config;
});

// Auto-authenticate as viewer if no token exists
export const autoAuthenticate = async () => {
  if (inMemoryToken) return inMemoryToken;
  try {
    const data = await loginApi('viewer', 'viewer123');
    if (data?.access_token) {
      setAccessToken(data.access_token);
      return data.access_token;
    }
  } catch (err) {
    console.warn('Auto-authentication failed or backend offline:', err.message);
  }
  return null;
};

// Auth
export const loginApi = async (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  const response = await apiClient.post('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  if (response.data?.access_token) {
    setAccessToken(response.data.access_token);
  }
  return response.data;
};

// System info & telemetry
export const fetchSystemInfo = async () => {
  const response = await apiClient.get('/system/info');
  return response.data;
};

// Reference data
export const fetchLeagues = async () => {
  const response = await apiClient.get('/leagues');
  return response.data;
};

export const fetchTeams = async (league = '') => {
  const url = league ? `/teams?league=${encodeURIComponent(league)}` : '/teams';
  const response = await apiClient.get(url);
  return response.data;
};

export const searchPlayers = async (query = '', league = '', limit = 15) => {
  const params = new URLSearchParams();
  if (query) params.append('search', query);
  if (league) params.append('league', league);
  if (limit) params.append('limit', limit);

  const response = await apiClient.get(`/players?${params.toString()}`);
  return response.data;
};

// Prediction
export const predictTransfer = async ({ player, source_league, target_league, target_team }) => {
  const response = await apiClient.post('/predict', {
    player,
    source_league,
    target_league,
    target_team,
  });
  return response.data;
};

// Benchmarks & audit logs
export const fetchBenchmarks = async (limit = 20) => {
  const response = await apiClient.get(`/benchmarks?limit=${limit}`);
  return response.data;
};

export const fetchPredictionHistory = async (limit = 10) => {
  const response = await apiClient.get(`/predictions/history?limit=${limit}`);
  return response.data;
};

export const fetchTestTransfers = async (limit = 100, search = '') => {
  const q = search ? `&search=${encodeURIComponent(search)}` : '';
  const response = await apiClient.get(`/transfers/test-set?limit=${limit}${q}`);
  return response.data;
};

