import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Home.css';

const Home: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="home-container">
      <div className="welcome-section">
        <h1>Benvenuto in NutrAICoach! 👋</h1>
        <p className="subtitle">Ciao {user?.username}, sono il tuo assistente nutrizionale personale.</p>
      </div>

      <div className="features-grid">
        <div className="feature-card">
          <div className="feature-icon">🥗</div>
          <h3>Piani Alimentari</h3>
          <p>Ricevi piani alimentari personalizzati basati sui tuoi obiettivi e preferenze.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">💬</div>
          <h3>Chat Assistente</h3>
          <p>Chatta con il tuo assistente AI per domande nutrizionali e consigli personalizzati.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Monitoraggio</h3>
          <p>Tieni traccia dei tuoi progressi e ricevi feedback personalizzati.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">⚙️</div>
          <h3>Personalizzazione</h3>
          <p>Configura le tue preferenze alimentari e i tuoi obiettivi di salute.</p>
        </div>
      </div>

      <div className="quick-actions">
        <h2>Inizia subito</h2>
        <div className="action-buttons">
          <button className="action-btn primary">
            <span>💬</span>
            Chatta con l'assistente
          </button>
          <button className="action-btn secondary">
            <span>🍽️</span>
            Visualizza la tua dieta
          </button>
        </div>
      </div>
    </div>
  );
};

export default Home; 