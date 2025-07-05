import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LogIn, User, Lock } from 'lucide-react';
import './Login.css';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      // Redirect dopo il login riuscito
      navigate('/home');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore durante il login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <LogIn className="login-icon" size={48} />
          <h1>NutrAICoach</h1>
          <p>Accedi al tuo account</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <div className="input-group">
              <User className="input-icon" size={20} />
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Inserisci il tuo username"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-group">
              <Lock className="input-icon" size={20} />
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Inserisci la tua password"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Accesso in corso...' : 'Accedi'}
          </button>
        </form>

        <div className="login-info">
          <h3>🔗 Connessione con Streamlit</h3>
          <p>
            Questo sistema React condivide i dati con l'applicazione Streamlit esistente. 
            Usa le stesse credenziali che utilizzi per accedere al sistema Streamlit.
          </p>
          <div className="features">
            <div className="feature">
              <span className="feature-icon">💾</span>
              <span>Dati condivisi con Streamlit</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🗣️</span>
              <span>Chat history sincronizzata</span>
            </div>
            <div className="feature">
              <span className="feature-icon">👤</span>
              <span>Account unificato</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login; 