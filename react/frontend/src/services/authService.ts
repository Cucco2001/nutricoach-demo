import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Configurazione axios
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor per aggiungere automaticamente il token di autenticazione
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor per gestire errori di autenticazione
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token scaduto o non valido
      localStorage.removeItem('token');
      window.location.href = '/login'; // Reindirizza al login
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  username: string;
  email?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  // Imposta il token di autenticazione
  setAuthToken: (token: string | null) => {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  },

  // Login utente
  login: async (username: string, password: string): Promise<LoginResponse> => {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', {
        username,
        password,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.detail || 'Login failed');
      }
      throw new Error('Network error');
    }
  },

  // Logout utente
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
      // Non lanciare errore per logout, potrebbero esserci problemi di rete
    }
  },

  // Ottieni informazioni utente corrente
  getCurrentUser: async (): Promise<User> => {
    try {
      const response = await apiClient.get<User>('/auth/me');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.detail || 'Failed to get user info');
      }
      throw new Error('Network error');
    }
  },

  // Controllo salute del server
  healthCheck: async (): Promise<boolean> => {
    try {
      await apiClient.get('/health');
      return true;
    } catch (error) {
      return false;
    }
  },
};

export default apiClient; 