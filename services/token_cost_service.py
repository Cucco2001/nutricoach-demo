"""
Servizio per il tracking dei token e calcolo dei costi delle conversazioni.

Questo modulo gestisce il conteggio dei token utilizzati durante le chat
e calcola i costi basati sui prezzi di OpenAI per GPT-4.
"""

import tiktoken
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class TokenCostTracker:
    """
    Tracker per monitorare l'utilizzo dei token e calcolare i costi.
    """
    
    # Prezzi OpenAI GPT-4 (al 25/06/2025)
    # Fonte: https://openai.com/pricing
    PRICING = {
        "gpt-4": {
            "input": 0.002,    # $ per 1K token
            "output": 0.008    # $ per 1K token
        },
        "gpt-4-turbo": {
            "input": 0.01,    # $ per 1K token
            "output": 0.03    # $ per 1K token
        },
        "gpt-4o": {
            "input": 0.005,   # $ per 1K token
            "output": 0.015   # $ per 1K token
        }
    }
    
    def __init__(self, model: str = "gpt-4"):
        """
        Inizializza il tracker.
        
        Args:
            model: Il modello OpenAI utilizzato (default: gpt-4)
        """
        self.model = model
        self.encoding = tiktoken.encoding_for_model("gpt-4")  # Usa encoding GPT-4
        self.conversation_tokens = {
            "input": 0,
            "output": 0,
            "total": 0
        }
        self.conversation_costs = {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0
        }
        self.message_count = 0
        self.start_time = datetime.now()
        
    def count_tokens(self, text: str) -> int:
        """
        Conta i token in un testo.
        
        Args:
            text: Il testo da analizzare
            
        Returns:
            int: Numero di token
        """
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            print(f"[TOKEN_COUNTER] Errore nel conteggio token: {e}")
            # Stima approssimativa: 1 token ≈ 4 caratteri
            return len(text) // 4
    
    def track_message(self, role: str, content: str) -> Dict[str, int]:
        """
        Traccia un singolo messaggio e aggiorna i contatori.
        
        Args:
            role: Ruolo del messaggio (user/assistant)
            content: Contenuto del messaggio
            
        Returns:
            Dict con token count per questo messaggio
        """
        tokens = self.count_tokens(content)
        
        if role == "user":
            self.conversation_tokens["input"] += tokens
        elif role == "assistant":
            self.conversation_tokens["output"] += tokens
            
        self.conversation_tokens["total"] += tokens
        self.message_count += 1
        
        # Aggiorna i costi
        self._update_costs()
        
        return {
            "tokens": tokens,
            "role": role,
            "cumulative_total": self.conversation_tokens["total"]
        }
    
    def _update_costs(self):
        """Aggiorna i costi basati sui token attuali."""
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4"])
        
        # Calcola costi in USD
        self.conversation_costs["input_cost"] = (
            self.conversation_tokens["input"] / 1000 * pricing["input"]
        )
        self.conversation_costs["output_cost"] = (
            self.conversation_tokens["output"] / 1000 * pricing["output"]
        )
        self.conversation_costs["total_cost"] = (
            self.conversation_costs["input_cost"] + 
            self.conversation_costs["output_cost"]
        )
    
    def get_conversation_stats(self) -> Dict:
        """
        Ottiene le statistiche complete della conversazione.
        
        Returns:
            Dict con tutte le statistiche
        """
        duration = (datetime.now() - self.start_time).total_seconds() / 60  # minuti
        
        return {
            "tokens": {
                "input": self.conversation_tokens["input"],
                "output": self.conversation_tokens["output"],
                "total": self.conversation_tokens["total"]
            },
            "costs": {
                "input_cost_usd": round(self.conversation_costs["input_cost"], 4),
                "output_cost_usd": round(self.conversation_costs["output_cost"], 4),
                "total_cost_usd": round(self.conversation_costs["total_cost"], 4),
                "total_cost_eur": round(self.conversation_costs["total_cost"] * 0.92, 4)  # Conversione approssimativa
            },
            "usage": {
                "message_count": self.message_count,
                "duration_minutes": round(duration, 2),
                "avg_tokens_per_message": round(
                    self.conversation_tokens["total"] / max(self.message_count, 1), 2
                )
            },
            "model": self.model,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cost_summary(self) -> str:
        """
        Ottiene un riepilogo leggibile dei costi.
        
        Returns:
            str: Riepilogo formattato
        """
        stats = self.get_conversation_stats()
        
        return f"""
💰 **Riepilogo Costi Conversazione**
- Token Input: {stats['tokens']['input']:,}
- Token Output: {stats['tokens']['output']:,}
- Token Totali: {stats['tokens']['total']:,}
- Costo: €{stats['costs']['total_cost_eur']:.3f} (${stats['costs']['total_cost_usd']:.3f})
- Messaggi: {stats['usage']['message_count']}
- Durata: {stats['usage']['duration_minutes']:.1f} minuti
"""
    
    def estimate_remaining_budget(self, budget_eur: float) -> Dict:
        """
        Stima quante conversazioni simili si possono fare con un budget.
        
        Args:
            budget_eur: Budget in EUR
            
        Returns:
            Dict con stime
        """
        current_cost_eur = self.conversation_costs["total_cost"] * 0.92
        
        if current_cost_eur == 0:
            return {"error": "Nessun costo ancora calcolato"}
        
        conversations_remaining = budget_eur / current_cost_eur
        
        return {
            "budget_eur": budget_eur,
            "cost_per_conversation_eur": round(current_cost_eur, 4),
            "conversations_remaining": int(conversations_remaining),
            "tokens_remaining": int(conversations_remaining * self.conversation_tokens["total"])
        } 