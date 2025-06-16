#!/usr/bin/env python3
"""
Script di utilità per la migrazione e gestione dei dati utente tra locale e Supabase.

Questo script permette di:
- Verificare la corrispondenza tra dati locali e Supabase
- Migrare tutti i dati da locale a Supabase
- Scaricare tutti i dati da Supabase a locale
- Confrontare e analizzare differenze
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List

# Aggiungi il path principale per gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import SupabaseUserService


class SupabaseMigrationManager:
    """Manager per la migrazione e verifica dei dati Supabase"""
    
    def __init__(self):
        """Inizializza il manager di migrazione"""
        self.supabase_service = SupabaseUserService()
        self.local_data_dir = "user_data"
    
    def verify_data_consistency(self) -> Dict[str, Any]:
        """
        Verifica la consistenza tra dati locali e Supabase.
        
        Returns:
            Dict con il report di verifica
        """
        print("🔍 Verifica consistenza dati locale ↔ Supabase...")
        
        if not self.supabase_service.is_available():
            return {"error": "Supabase non disponibile"}
        
        # Carica dati locali
        local_users = self._load_local_users()
        local_user_data = self._load_local_user_data()
        
        # Carica dati Supabase
        supabase_users = self.supabase_service.download_users_from_supabase() or {}
        supabase_user_data = self.supabase_service.download_all_user_data_from_supabase()
        
        # Confronta
        report = {
            "timestamp": datetime.now().isoformat(),
            "supabase_available": True,
            "local_users_count": len(local_users),
            "supabase_users_count": len(supabase_users),
            "local_user_data_count": len(local_user_data),
            "supabase_user_data_count": len(supabase_user_data),
            "users_comparison": self._compare_users(local_users, supabase_users),
            "user_data_comparison": self._compare_user_data(local_user_data, supabase_user_data),
            "recommendations": []
        }
        
        # Genera raccomandazioni
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def migrate_all_to_supabase(self, force: bool = False) -> bool:
        """
        Migra tutti i dati locali su Supabase.
        
        Args:
            force: Se True, sovrascrive i dati esistenti su Supabase
            
        Returns:
            bool: True se la migrazione è riuscita
        """
        print("📤 Migrazione completa locale → Supabase...")
        
        if not self.supabase_service.is_available():
            print("❌ Supabase non disponibile")
            return False
        
        if not force:
            # Verifica se ci sono già dati su Supabase
            existing_users = self.supabase_service.download_users_from_supabase()
            if existing_users and len(existing_users) > 0:
                response = input(f"⚠️ Trovati {len(existing_users)} utenti su Supabase. Continuare? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Migrazione annullata")
                    return False
        
        success = self.supabase_service.sync_all_local_data_to_supabase()
        
        if success:
            print("✅ Migrazione completa riuscita")
        else:
            print("❌ Migrazione fallita o parziale")
        
        return success
    
    def download_all_from_supabase(self, force: bool = False) -> bool:
        """
        Scarica tutti i dati da Supabase e li salva localmente.
        
        Args:
            force: Se True, sovrascrive i dati locali esistenti
            
        Returns:
            bool: True se il download è riuscito
        """
        print("📥 Download completo Supabase → locale...")
        
        if not self.supabase_service.is_available():
            print("❌ Supabase non disponibile")
            return False
        
        if not force:
            # Verifica se ci sono già dati locali
            local_users = self._load_local_users()
            if local_users and len(local_users) > 0:
                response = input(f"⚠️ Trovati {len(local_users)} utenti locali. Sovrascrivere? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Download annullato")
                    return False
        
        success = self.supabase_service.download_all_data_from_supabase()
        
        if success:
            print("✅ Download completo riuscito")
        else:
            print("❌ Download fallito o parziale")
        
        return success
    
    def compare_csv_files(self) -> Dict[str, Any]:
        """
        Confronta i file CSV esistenti con i dati su Supabase.
        
        Returns:
            Dict con il report di confronto
        """
        print("📊 Confronto file CSV con Supabase...")
        
        report = {
            "users_csv": self._compare_users_csv(),
            "user_data_csv": self._compare_user_data_csv()
        }
        
        return report
    
    def _load_local_users(self) -> Dict[str, Any]:
        """Carica gli utenti dal file locale users.json"""
        users_file = os.path.join(self.local_data_dir, "users.json")
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_local_user_data(self) -> Dict[str, Any]:
        """Carica tutti i dati utente dai file JSON locali"""
        user_data = {}
        if os.path.exists(self.local_data_dir):
            for filename in os.listdir(self.local_data_dir):
                if filename.endswith(".json") and filename != "users.json":
                    user_id = filename.replace(".json", "")
                    try:
                        with open(os.path.join(self.local_data_dir, filename), 'r', encoding='utf-8') as f:
                            user_data[user_id] = json.load(f)
                    except Exception as e:
                        print(f"⚠️ Errore caricamento {filename}: {str(e)}")
        return user_data
    
    def _compare_users(self, local: Dict, supabase: Dict) -> Dict[str, Any]:
        """Confronta gli utenti tra locale e Supabase"""
        local_usernames = set(local.keys())
        supabase_usernames = set(supabase.keys())
        
        return {
            "only_local": list(local_usernames - supabase_usernames),
            "only_supabase": list(supabase_usernames - local_usernames),
            "common": list(local_usernames & supabase_usernames),
            "differences": self._find_user_differences(local, supabase)
        }
    
    def _compare_user_data(self, local: Dict, supabase: Dict) -> Dict[str, Any]:
        """Confronta i dati utente tra locale e Supabase"""
        local_user_ids = set(local.keys())
        supabase_user_ids = set(supabase.keys())
        
        return {
            "only_local": list(local_user_ids - supabase_user_ids),
            "only_supabase": list(supabase_user_ids - local_user_ids),
            "common": list(local_user_ids & supabase_user_ids),
            "data_size_differences": self._find_data_size_differences(local, supabase)
        }
    
    def _find_user_differences(self, local: Dict, supabase: Dict) -> List[Dict[str, Any]]:
        """Trova differenze nei dati utente comuni"""
        differences = []
        
        for username in set(local.keys()) & set(supabase.keys()):
            local_user = local[username]
            supabase_user = supabase[username]
            
            diff = {}
            for key in ["password_hash", "user_id", "created_at"]:
                if key in local_user and key in supabase_user:
                    if local_user[key] != supabase_user[key]:
                        diff[key] = {
                            "local": local_user[key],
                            "supabase": supabase_user[key]
                        }
            
            if diff:
                differences.append({"username": username, "differences": diff})
        
        return differences
    
    def _find_data_size_differences(self, local: Dict, supabase: Dict) -> List[Dict[str, Any]]:
        """Trova differenze nelle dimensioni dei dati utente"""
        differences = []
        
        for user_id in set(local.keys()) & set(supabase.keys()):
            local_size = len(json.dumps(local[user_id]))
            supabase_size = len(json.dumps(supabase[user_id]))
            
            if abs(local_size - supabase_size) > 100:  # Differenza significativa > 100 caratteri
                differences.append({
                    "user_id": user_id,
                    "local_size": local_size,
                    "supabase_size": supabase_size,
                    "difference": abs(local_size - supabase_size)
                })
        
        return differences
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Genera raccomandazioni basate sul report di verifica"""
        recommendations = []
        
        users_comp = report["users_comparison"]
        data_comp = report["user_data_comparison"]
        
        if users_comp["only_local"]:
            recommendations.append(f"📤 {len(users_comp['only_local'])} utenti presenti solo in locale - considera di caricarli su Supabase")
        
        if users_comp["only_supabase"]:
            recommendations.append(f"📥 {len(users_comp['only_supabase'])} utenti presenti solo su Supabase - considera di scaricarli in locale")
        
        if data_comp["only_local"]:
            recommendations.append(f"📤 {len(data_comp['only_local'])} file dati presenti solo in locale - considera di caricarli su Supabase")
        
        if data_comp["only_supabase"]:
            recommendations.append(f"📥 {len(data_comp['only_supabase'])} file dati presenti solo su Supabase - considera di scaricarli in locale")
        
        if users_comp["differences"]:
            recommendations.append(f"⚠️ {len(users_comp['differences'])} utenti con differenze nei dati - verifica manualmente")
        
        if data_comp["data_size_differences"]:
            recommendations.append(f"⚠️ {len(data_comp['data_size_differences'])} utenti con differenze significative nei dati - verifica manualmente")
        
        if not recommendations:
            recommendations.append("✅ Dati in sincronizzazione perfetta!")
        
        return recommendations
    
    def _compare_users_csv(self) -> Dict[str, Any]:
        """Confronta users_rows.csv con Supabase"""
        csv_file = "users_rows.csv"
        if not os.path.exists(csv_file):
            return {"error": "File users_rows.csv non trovato"}
        
        try:
            # Leggi CSV
            df = pd.read_csv(csv_file)
            csv_users = {}
            for _, row in df.iterrows():
                csv_users[row['username']] = {
                    "username": row['username'],
                    "password_hash": row['password_hash'],
                    "user_id": row['user_id'],
                    "created_at": row['created_at']
                }
            
            # Confronta con Supabase
            supabase_users = self.supabase_service.download_users_from_supabase() or {}
            
            return {
                "csv_count": len(csv_users),
                "supabase_count": len(supabase_users),
                "matching": len(set(csv_users.keys()) & set(supabase_users.keys())),
                "only_csv": list(set(csv_users.keys()) - set(supabase_users.keys())),
                "only_supabase": list(set(supabase_users.keys()) - set(csv_users.keys()))
            }
            
        except Exception as e:
            return {"error": f"Errore lettura CSV: {str(e)}"}
    
    def _compare_user_data_csv(self) -> Dict[str, Any]:
        """Confronta user_data_rows.csv con Supabase"""
        csv_file = "user_data_rows.csv"
        if not os.path.exists(csv_file):
            return {"error": "File user_data_rows.csv non trovato"}
        
        try:
            # Leggi CSV
            df = pd.read_csv(csv_file)
            csv_user_data = {}
            for _, row in df.iterrows():
                csv_user_data[row['user_id']] = json.loads(row['data'])
            
            # Confronta con Supabase
            supabase_user_data = self.supabase_service.download_all_user_data_from_supabase()
            
            return {
                "csv_count": len(csv_user_data),
                "supabase_count": len(supabase_user_data),
                "matching": len(set(csv_user_data.keys()) & set(supabase_user_data.keys())),
                "only_csv": list(set(csv_user_data.keys()) - set(supabase_user_data.keys())),
                "only_supabase": list(set(supabase_user_data.keys()) - set(csv_user_data.keys()))
            }
            
        except Exception as e:
            return {"error": f"Errore lettura CSV: {str(e)}"}


def main():
    """Funzione principale per l'esecuzione da linea di comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestione migrazione dati Supabase")
    parser.add_argument("command", choices=[
        "verify", "migrate-to-supabase", "download-from-supabase", "compare-csv"
    ], help="Comando da eseguire")
    parser.add_argument("--force", action="store_true", help="Forza l'operazione senza conferma")
    
    args = parser.parse_args()
    
    manager = SupabaseMigrationManager()
    
    if args.command == "verify":
        report = manager.verify_data_consistency()
        print("\n" + "="*60)
        print("📊 REPORT VERIFICA CONSISTENZA")
        print("="*60)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
    elif args.command == "migrate-to-supabase":
        success = manager.migrate_all_to_supabase(force=args.force)
        sys.exit(0 if success else 1)
        
    elif args.command == "download-from-supabase":
        success = manager.download_all_from_supabase(force=args.force)
        sys.exit(0 if success else 1)
        
    elif args.command == "compare-csv":
        report = manager.compare_csv_files()
        print("\n" + "="*60)
        print("📊 CONFRONTO FILE CSV")
        print("="*60)
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main() 