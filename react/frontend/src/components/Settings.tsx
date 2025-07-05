import React from 'react';
import './Settings.css';

const Settings: React.FC = () => {
  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>⚙️ Impostazioni</h1>
        <p className="subtitle">Personalizza la tua esperienza</p>
      </div>

      <div className="coming-soon">
        <div className="coming-soon-content">
          <div className="coming-soon-icon">🚧</div>
          <h2>Sezione in Sviluppo</h2>
          <p>
            Questa sezione è in fase di sviluppo. Qui potrai personalizzare 
            le tue preferenze e impostazioni.
          </p>
          <div className="planned-features">
            <h3>Funzionalità in arrivo:</h3>
            <ul>
              <li>👤 Profilo utente</li>
              <li>🥗 Preferenze alimentari</li>
              <li>🎯 Obiettivi di salute</li>
              <li>📊 Parametri fisici</li>
              <li>🔔 Notifiche</li>
              <li>🌙 Tema scuro/chiaro</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings; 