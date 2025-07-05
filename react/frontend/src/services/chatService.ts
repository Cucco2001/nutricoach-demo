import apiClient from './authService';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface SendMessageRequest {
  message: string;
}

export interface SendMessageResponse {
  response: string;
  message_id?: string;
}

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export const chatService = {
  // Invia un messaggio all'assistente
  sendMessage: async (message: string): Promise<SendMessageResponse> => {
    try {
      const response = await apiClient.post<SendMessageResponse>('/chat/send', {
        message,
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  // Recupera la cronologia della chat
  getChatHistory: async (): Promise<{ messages: ChatMessage[] }> => {
    try {
      const response = await apiClient.get<ChatHistoryItem[]>('/chat/history');
      // Converto la struttura del backend al formato del frontend
      const messages: ChatMessage[] = response.data.map(item => ({
        role: item.role,
        content: item.content,
        timestamp: new Date(item.timestamp * 1000) // Converto timestamp Unix a Date
      }));
      return { messages };
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw error;
    }
  },

  // Cancella la cronologia della chat
  clearChatHistory: async (): Promise<void> => {
    try {
      await apiClient.delete('/chat/clear');
    } catch (error) {
      console.error('Error clearing chat history:', error);
      throw error;
    }
  },

  // Crea un nuovo thread di conversazione
  createNewThread: async (): Promise<string> => {
    try {
      const response = await apiClient.post<{ thread_id: string }>('/chat/thread/create');
      return response.data.thread_id;
    } catch (error) {
      console.error('Error creating new thread:', error);
      throw error;
    }
  },

  // Ottieni il thread corrente
  getCurrentThread: async (): Promise<string> => {
    try {
      const response = await apiClient.get<{ thread_id: string }>('/chat/thread/current');
      return response.data.thread_id;
    } catch (error) {
      console.error('Error getting current thread:', error);
      throw error;
    }
  },
}; 