import React from 'react';
import './Diet.css';

const Diet: React.FC = () => {
  return (
    <div className="diet-container">
      <div className="diet-header">
        <h1>🍽️ Piano Nutrizionale</h1>
        <p className="subtitle">Il tuo piano alimentare personalizzato</p>
      </div>

      <div className="coming-soon">
        <div className="coming-soon-content">
          <div className="coming-soon-icon">🚧</div>
          <h2>Sezione in Sviluppo</h2>
          <p>
            Questa sezione è in fase di sviluppo. Qui potrai visualizzare e gestire 
            i tuoi piani alimentari personalizzati.
          </p>
          <div className="planned-features">
            <h3>Funzionalità in arrivo:</h3>
            <ul>
              <li>📋 Visualizzazione piano settimanale</li>
              <li>🔄 Sostituzione alimenti</li>
              <li>📊 Analisi nutrizionale</li>
              <li>🛒 Lista della spesa</li>
              <li>📱 Esportazione PDF</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Diet; 