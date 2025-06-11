#!/usr/bin/env python3
"""
Genera una dieta completa settimanale (giorni 1-7) e salva l'output in un file txt
"""

import json
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.weekly_diet_generator_tool import generate_6_additional_days, extract_day1_meal_structure

def format_meal_output(meal_name, meal_data, day_num):
    """Formatta l'output di un singolo pasto"""
    output = []
    
    if isinstance(meal_data, dict) and "error" in meal_data:
        output.append(f"   ❌ {meal_name.upper()}: ERRORE - {meal_data.get('error', 'Sconosciuto')}")
        return "\n".join(output)
    
    if not meal_data or (isinstance(meal_data, dict) and not meal_data.get("alimenti")):
        output.append(f"   ⭕ {meal_name.upper()}: PASTO VUOTO")
        return "\n".join(output)
    
    # Header del pasto
    output.append(f"   🍽️  {meal_name.upper()}")
    
    if isinstance(meal_data, dict):
        alimenti = meal_data.get("alimenti", {})
        target_nutrients = meal_data.get("target_nutrients", {})
        actual_nutrients = meal_data.get("actual_nutrients", {})
        optimization_summary = meal_data.get("optimization_summary", "")
        
        # Alimenti e porzioni
        if alimenti:
            output.append("      📋 ALIMENTI:")
            for food, amount in alimenti.items():
                output.append(f"         • {food}: {amount}g")
        
        # Target vs Actual
        if target_nutrients and actual_nutrients:
            output.append("      📊 NUTRIENTI:")
            for nutrient in ['kcal', 'proteine_g', 'carboidrati_g', 'grassi_g']:
                target_val = target_nutrients.get(nutrient, 0)
                actual_val = actual_nutrients.get(nutrient, 0)
                if target_val > 0:
                    error_pct = abs(actual_val - target_val) / target_val * 100
                    status = "✅" if error_pct < 10 else "⚠️" if error_pct < 20 else "❌"
                    output.append(f"         {status} {nutrient}: {actual_val:.1f} / {target_val:.1f} target ({error_pct:.1f}% errore)")
        
        # Summary ottimizzazione
        if optimization_summary:
            output.append(f"      💡 {optimization_summary}")
    
    return "\n".join(output)

def format_day1_from_user_data(user_id):
    """Formatta il giorno 1 dai dati utente"""
    output = []
    
    try:
        # Carica i dati dell'utente
        user_file_path = f"user_data/user_{user_id}.json"
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        registered_meals = nutritional_info.get("registered_meals", [])
        daily_macros = nutritional_info.get("daily_macros", {})
        
        output.append("📅 GIORNO 1 - DATI UTENTE REGISTRATI")
        output.append("=" * 80)
        
        # Organizza i pasti per tipo
        meals_by_type = {}
        for meal in registered_meals:
            meal_type = meal.get("nome_pasto", "sconosciuto")
            if meal_type not in meals_by_type:
                meals_by_type[meal_type] = []
            meals_by_type[meal_type].extend(meal.get("alimenti", []))
        
        # Distribuzione target
        distribuzione_pasti = daily_macros.get("distribuzione_pasti", {})
        
        # Mostra ogni pasto
        standard_meals = ["colazione", "spuntino_mattutino", "pranzo", "spuntino_pomeridiano", "cena", "spuntino_serale"]
        
        for meal_name in standard_meals:
            if meal_name in meals_by_type and meals_by_type[meal_name]:
                output.append(f"\n   🍽️  {meal_name.upper()}")
                output.append("      📋 ALIMENTI REGISTRATI:")
                
                for alimento in meals_by_type[meal_name]:
                    nome = alimento.get("nome_alimento", "N/A")
                    quantita = alimento.get("quantita_g", 0)
                    if quantita > 0:
                        output.append(f"         • {nome}: {quantita}g")
                
                # Target per questo pasto
                if meal_name in distribuzione_pasti:
                    target_data = distribuzione_pasti[meal_name]
                    output.append("      🎯 TARGET NUTRIZIONALI:")
                    output.append(f"         • Calorie: {target_data.get('kcal', 0)}")
                    output.append(f"         • Proteine: {target_data.get('proteine_g', 0)}g")
                    output.append(f"         • Carboidrati: {target_data.get('carboidrati_g', 0)}g")
                    output.append(f"         • Grassi: {target_data.get('grassi_g', 0)}g")
                    output.append(f"         • Orario: {target_data.get('orario', 'N/A')}")
            else:
                output.append(f"\n   ⭕ {meal_name.upper()}: PASTO VUOTO")
        
        # Totali giornalieri
        total_macros = daily_macros.get("totali_giornalieri", {})
        if total_macros:
            output.append(f"\n   📈 TOTALI GIORNALIERI:")
            output.append(f"      • Calorie totali: {total_macros.get('kcal_totali', 0)}")
            output.append(f"      • Proteine totali: {total_macros.get('proteine_totali', 0)}g")
            output.append(f"      • Carboidrati totali: {total_macros.get('carboidrati_totali', 0)}g")
            output.append(f"      • Grassi totali: {total_macros.get('grassi_totali', 0)}g")
        
    except Exception as e:
        output.append(f"❌ ERRORE nel caricamento giorno 1: {str(e)}")
    
    return "\n".join(output)

def generate_complete_weekly_diet(user_id):
    """Genera la dieta completa settimanale"""
    
    print(f"🔄 Generazione dieta settimanale per utente {user_id}...")
    
    # Header del file
    output = []
    output.append("🍽️" * 20)
    output.append("DIETA SETTIMANALE COMPLETA - GENERATA AUTOMATICAMENTE")
    output.append("🍽️" * 20)
    output.append(f"")
    output.append(f"📊 INFORMAZIONI GENERAZIONE:")
    output.append(f"   • User ID: {user_id}")
    output.append(f"   • Data generazione: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"   • Pipeline: extract_day1_meal_structure → generate_6_additional_days")
    output.append(f"")
    
    # GIORNO 1 - Dati utente
    output.append(format_day1_from_user_data(user_id))
    output.append("")
    
    # GIORNI 2-7 - Generati automaticamente
    try:
        print("🔄 Chiamata generate_6_additional_days...")
        result = generate_6_additional_days(user_id=user_id)
        
        if result.get('success'):
            output.append("📅 GIORNI 2-7 - GENERATI AUTOMATICAMENTE")
            output.append("=" * 80)
            
            giorni_generati = result.get("giorni_generati", {})
            
            # Statistiche generali
            total_days = len(giorni_generati)
            total_meals = 0
            successful_meals = 0
            
            for day_key in sorted(giorni_generati.keys()):
                day_data = giorni_generati[day_key]
                day_num = day_key.replace("giorno_", "")
                
                output.append(f"\n📅 GIORNO {day_num}")
                output.append("-" * 40)
                
                if not day_data:
                    output.append("   ⭕ GIORNO VUOTO")
                    continue
                
                # Ordine standard dei pasti
                standard_meals = ["colazione", "spuntino_mattutino", "pranzo", "spuntino_pomeridiano", "cena", "spuntino_serale"]
                
                for meal_name in standard_meals:
                    if meal_name in day_data:
                        total_meals += 1
                        meal_data = day_data[meal_name]
                        
                        if isinstance(meal_data, dict) and "error" not in meal_data and meal_data.get("alimenti"):
                            successful_meals += 1
                        
                        output.append(format_meal_output(meal_name, meal_data, day_num))
                        output.append("")
            
            # Statistiche finali
            success_rate = (successful_meals / total_meals * 100) if total_meals > 0 else 0
            output.append("\n" + "📈" * 20)
            output.append("STATISTICHE GENERAZIONE")
            output.append("📈" * 20)
            output.append(f"")
            output.append(f"📊 RIEPILOGO:")
            output.append(f"   • Giorni generati: {total_days + 1} (1 da dati utente + {total_days} automatici)")
            output.append(f"   • Pasti processati: {total_meals}")
            output.append(f"   • Pasti ottimizzati con successo: {successful_meals}")
            output.append(f"   • Tasso di successo: {success_rate:.1f}%")
            output.append(f"")
            output.append(f"✅ Generazione completata con successo!")
            
        else:
            error_msg = result.get('error', 'Errore sconosciuto')
            output.append(f"❌ ERRORE nella generazione giorni 2-7: {error_msg}")
            
    except Exception as e:
        output.append(f"❌ ERRORE CRITICO: {str(e)}")
        import traceback
        output.append(f"Traceback: {traceback.format_exc()}")
    
    return "\n".join(output)

def main():
    """Funzione principale"""
    
    # Utente per il test
    test_user_id = "1749309652"
    output_filename = f"dieta_settimanale_user_{test_user_id}.txt"
    
    print("🍽️" * 10)
    print("GENERAZIONE DIETA SETTIMANALE COMPLETA")
    print("🍽️" * 10)
    print(f"")
    print(f"📋 Parametri:")
    print(f"   • User ID: {test_user_id}")
    print(f"   • Output file: {output_filename}")
    print(f"")
    
    # Genera la dieta completa
    diet_content = generate_complete_weekly_diet(test_user_id)
    
    # Salva nel file
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(diet_content)
        
        print(f"✅ Dieta settimanale salvata in: {output_filename}")
        print(f"📄 Dimensione file: {len(diet_content)} caratteri")
        
        # Mostra un preview
        lines = diet_content.split('\n')
        print(f"")
        print("📖 PREVIEW (prime 20 righe):")
        print("-" * 50)
        for i, line in enumerate(lines[:20]):
            print(line)
        if len(lines) > 20:
            print(f"... (+{len(lines) - 20} righe)")
        
    except Exception as e:
        print(f"❌ Errore nel salvataggio: {str(e)}")

if __name__ == "__main__":
    main() 