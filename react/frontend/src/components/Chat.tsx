import React, { useState, useEffect, useRef } from 'react';
import { chatService } from '../services/chatService';
import type { ChatMessage } from '../services/chatService';
import { Send, Trash2, RotateCcw } from 'lucide-react';
import './Chat.css';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scorri automaticamente verso il basso quando ci sono nuovi messaggi
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Carica la cronologia dei messaggi al mount del componente
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const history = await chatService.getChatHistory();
      setMessages(history.messages);
    } catch (err) {
      console.error('Error loading chat history:', err);
      setError('Errore nel caricamento della cronologia');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // Aggiungi il messaggio dell'utente immediatamente
    const newUserMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    setIsLoading(true);

    try {
      // Invia il messaggio al backend
      const response = await chatService.sendMessage(userMessage);
      
      // Aggiungi la risposta dell'assistente
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);

    } catch (err) {
      console.error('Error sending message:', err);
      setError('Errore nell\'invio del messaggio. Riprova.');
      
      // Rimuovi il messaggio dell'utente in caso di errore
      setMessages(prev => prev.slice(0, -1));
      setInputMessage(userMessage); // Ripristina il messaggio nell'input
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Sei sicuro di voler cancellare tutta la cronologia della chat?')) {
      try {
        await chatService.clearChatHistory();
        setMessages([]);
        setError(null);
      } catch (err) {
        console.error('Error clearing chat history:', err);
        setError('Errore nella cancellazione della cronologia');
      }
    }
  };

  const handleNewThread = async () => {
    try {
      await chatService.createNewThread();
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error('Error creating new thread:', err);
      setError('Errore nella creazione del nuovo thread');
    }
  };

  const formatTimestamp = (timestamp: Date | undefined) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString('it-IT', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>💬 Chat con l'Assistente</h1>
        <div className="chat-actions">
          <button 
            onClick={handleNewThread}
            className="action-btn secondary"
            title="Nuova conversazione"
          >
            <RotateCcw size={18} />
            <span>Nuova conversazione</span>
          </button>
          <button 
            onClick={handleClearHistory}
            className="action-btn danger"
            title="Cancella cronologia"
          >
            <Trash2 size={18} />
            <span>Cancella cronologia</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-icon">🤖</div>
            <h3>Benvenuto nella chat!</h3>
            <p>Inizia una conversazione con il tuo assistente nutrizionale personale.</p>
            <div className="suggested-questions">
              <h4>Domande suggerite:</h4>
              <button 
                onClick={() => setInputMessage("Ciao! Potresti aiutarmi con un piano alimentare?")}
                className="suggestion-btn"
              >
                Aiutami con un piano alimentare
              </button>
              <button 
                onClick={() => setInputMessage("Quali sono i benefici della dieta mediterranea?")}
                className="suggestion-btn"
              >
                Benefici della dieta mediterranea
              </button>
              <button 
                onClick={() => setInputMessage("Come posso calcolare il mio fabbisogno calorico?")}
                className="suggestion-btn"
              >
                Calcolo fabbisogno calorico
              </button>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-role">
                    {message.role === 'user' ? '👤 Tu' : '🤖 Assistente'}
                  </span>
                  <span className="message-time">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
                <div className="message-text">
                  {message.content}
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="message assistant loading">
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">🤖 Assistente</span>
              </div>
              <div className="message-text">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className="chat-input-form">
        <div className="input-container">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Scrivi un messaggio..."
            className="message-input"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="send-btn"
            disabled={isLoading || !inputMessage.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
};

export default Chat; 