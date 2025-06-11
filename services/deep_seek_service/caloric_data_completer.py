"""
Servizio per il completamento dei dati nutrizionali mancanti.

Questo modulo completa i dati che DeepSeek non è riuscito ad estrarre,
utilizzando gli stessi algoritmi e funzioni dell'agente NutriCoach.
"""

import json
import os
from typing import Dict, Any, Optional, List
from agent_tools.nutridb import NutriDB
from agent_tools.nutridb_tool import compute_Harris_Benedict_Equation, calculate_sport_expenditure
from .field_mapper import FieldMapper, get_field, set_field, has_field, ensure_section


class CaloricDataCompleter:
    """
    Completa i dati nutrizionali mancanti dall'estrazione di DeepSeek.
    
    Calcola:
    - BMR (metabolismo basale) usando Harris-Benedict
    - Fabbisogno base usando LAF appropriato  
    - Dispendio sportivo dai dati sport utente
    - Deficit/surplus calorico per obiettivi
    
    Utilizza un sistema di mappatura flessibile per gestire variazioni
    nei nomi dei campi estratti da DeepSeek.
    """
    
    def __init__(self):
        self.nutri_db = NutriDB("Dati_processed")
        self.field_mapper = FieldMapper()
        
    def complete_caloric_data(
        self, 
        user_id: str, 
        user_info: Dict[str, Any], 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Completa i dati calorici mancanti nell'estrazione di DeepSeek.
        
        Args:
            user_id: ID dell'utente
            user_info: Dati utente con nutritional_info
            extracted_data: Dati estratti da DeepSeek
            
        Returns:
            Dati estratti completati con i valori mancanti
        """
        print(f"[CALORIC_COMPLETER] Completamento dati per utente {user_id}")
        
        # Copia i dati per non modificare l'originale
        completed_data = extracted_data.copy()
        
        # Trova o crea la sezione caloric_needs usando il mapper
        caloric_section_name = ensure_section(completed_data, "caloric_needs")
        caloric_data = completed_data[caloric_section_name]
        
        # Debug: mostra quali campi sono già presenti
        debug_info = self.field_mapper.debug_available_fields(caloric_data)
        print(f"[CALORIC_COMPLETER] Campi disponibili: {debug_info.get('available_keys', [])}")
        print(f"[CALORIC_COMPLETER] Campi mappati: {debug_info.get('mapped_fields', {})}")
        
        # Estrai informazioni utente necessarie
        user_basic_info = self._extract_user_basic_info(user_info)
        if not user_basic_info:
            print(f"[CALORIC_COMPLETER] Informazioni utente incomplete per {user_id}")
            return completed_data
            
        # Calcola BMR e fabbisogno base usando la funzione originale dell'agente
        harris_benedict_result = self._calculate_harris_benedict()
        if harris_benedict_result:
            if not has_field(caloric_data, 'bmr'):
                set_field(caloric_data, 'bmr', harris_benedict_result.get('bmr'))
                print(f"[CALORIC_COMPLETER] BMR calcolato: {harris_benedict_result.get('bmr')} kcal")
            else:
                existing_bmr = get_field(caloric_data, 'bmr')
                print(f"[CALORIC_COMPLETER] BMR già presente: {existing_bmr} kcal")
            
            if not has_field(caloric_data, 'laf_utilizzato'):
                set_field(caloric_data, 'laf_utilizzato', harris_benedict_result.get('laf_utilizzato'))
                print(f"[CALORIC_COMPLETER] LAF impostato: {harris_benedict_result.get('laf_utilizzato')}")
            else:
                existing_laf = get_field(caloric_data, 'laf_utilizzato')
                print(f"[CALORIC_COMPLETER] LAF già presente: {existing_laf}")
            
            if not has_field(caloric_data, 'fabbisogno_base'):
                set_field(caloric_data, 'fabbisogno_base', harris_benedict_result.get('fabbisogno_giornaliero'))
                print(f"[CALORIC_COMPLETER] Fabbisogno base calcolato: {harris_benedict_result.get('fabbisogno_giornaliero')} kcal")
            else:
                existing_fabbisogno = get_field(caloric_data, 'fabbisogno_base')
                print(f"[CALORIC_COMPLETER] Fabbisogno base già presente: {existing_fabbisogno} kcal")
        
        # Calcola dispendio sportivo usando la funzione originale dell'agente
        if not has_field(caloric_data, 'dispendio_sportivo'):
            dispendio_sportivo = self._calculate_sport_expenditure_original(user_info)
            if dispendio_sportivo is not None:
                set_field(caloric_data, 'dispendio_sportivo', dispendio_sportivo)
                print(f"[CALORIC_COMPLETER] Dispendio sportivo calcolato: {dispendio_sportivo} kcal")
        else:
            existing_dispendio = get_field(caloric_data, 'dispendio_sportivo')
            print(f"[CALORIC_COMPLETER] Dispendio sportivo già presente: {existing_dispendio} kcal")
        
        # Calcola fabbisogno totale se mancante o incompleto
        fabbisogno_base = get_field(caloric_data, 'fabbisogno_base', 0)
        dispendio_sportivo = get_field(caloric_data, 'dispendio_sportivo', 0)
        
        if not has_field(caloric_data, 'fabbisogno_totale') and fabbisogno_base:
            fabbisogno_totale = fabbisogno_base + dispendio_sportivo
            set_field(caloric_data, 'fabbisogno_totale', fabbisogno_totale)
            print(f"[CALORIC_COMPLETER] Fabbisogno totale calcolato: {fabbisogno_totale} kcal")
        else:
            existing_totale = get_field(caloric_data, 'fabbisogno_totale')
            if existing_totale:
                print(f"[CALORIC_COMPLETER] Fabbisogno totale già presente: {existing_totale} kcal")
        
        # Calcola aggiustamento obiettivo se mancante
        if not has_field(caloric_data, 'aggiustamento_obiettivo'):
            bmr_value = get_field(caloric_data, 'bmr')
            aggiustamento = self._calculate_goal_adjustment(user_info, bmr_value)
            if aggiustamento is not None:
                set_field(caloric_data, 'aggiustamento_obiettivo', aggiustamento)
                print(f"[CALORIC_COMPLETER] Aggiustamento obiettivo: {aggiustamento} kcal")
        else:
            existing_aggiustamento = get_field(caloric_data, 'aggiustamento_obiettivo')
            print(f"[CALORIC_COMPLETER] Aggiustamento già presente: {existing_aggiustamento} kcal")
        
        return completed_data
    
    def _extract_user_basic_info(self, user_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Estrae le informazioni di base dell'utente necessarie per i calcoli.
        
        Args:
            user_info: Dati completi dell'utente
            
        Returns:
            Dizionario con età, sesso, peso, altezza, attività, obiettivo
        """
        try:
            nutritional_info = user_info.get('nutritional_info')
            if not nutritional_info:
                return None
                
            return {
                'età': nutritional_info.get('età'),
                'sesso': nutritional_info.get('sesso'),
                'peso': nutritional_info.get('peso'),
                'altezza': nutritional_info.get('altezza'),
                'attività': nutritional_info.get('attività'),
                'obiettivo': nutritional_info.get('obiettivo'),
                'nutrition_answers': nutritional_info.get('nutrition_answers', {})
            }
        except Exception as e:
            print(f"[CALORIC_COMPLETER] Errore estrazione info utente: {str(e)}")
            return None
    
    def _calculate_harris_benedict(self) -> Optional[Dict[str, Any]]:
        """
        Calcola BMR e fabbisogno base usando la funzione originale dell'agente.
        Usa automaticamente l'utente corrente in sessione.
            
        Returns:
            Risultato della funzione compute_Harris_Benedict_Equation
        """
        try:
            # Chiama la funzione aggiornata che estrae automaticamente i dati dal file utente
            result = compute_Harris_Benedict_Equation()
            
            # Verifica se c'è stato un errore
            if 'error' in result:
                print(f"[CALORIC_COMPLETER] Errore in Harris-Benedict: {result['error']}")
                return None
                
            print(f"[CALORIC_COMPLETER] Harris-Benedict calcolato con successo")
            return result
            
        except Exception as e:
            print(f"[CALORIC_COMPLETER] Errore nel calcolo Harris-Benedict: {str(e)}")
            return None
    
    def _calculate_sport_expenditure_original(self, user_info: Dict[str, Any]) -> Optional[int]:
        """
        Calcola il dispendio sportivo usando la funzione originale dell'agente.
        
        Args:
            user_info: Informazioni complete dell'utente
            
        Returns:
            Dispendio sportivo medio giornaliero in kcal
        """
        try:
            # Estrai informazioni sport dalle nutrition_answers
            nutritional_info = user_info.get('nutritional_info', {})
            nutrition_answers = nutritional_info.get('nutrition_answers', {})
            sports_info = nutrition_answers.get('sports', {})
            
            if not sports_info or sports_info.get('answer', '').lower() != 'sì':
                return 0
            
            sports_list = sports_info.get('follow_up', [])
            if not sports_list:
                return 0
            
            # Prepara i dati nel formato richiesto dalla funzione originale
            sports_for_calculation = []
            
            for sport_entry in sports_list:
                sport_info = sport_entry.get('specific_sport', {})
                sport_name = sport_info.get('key', sport_info.get('name', 'unknown'))
                hours = sport_entry.get('hours_per_week', 0)
                intensity = sport_entry.get('intensity', 'medium')
                
                print(f"[DEBUG] Ricevuto sport_name: '{sport_name}' (tipo: {type(sport_name)})")
                
                if sport_name and hours:
                    sports_for_calculation.append({
                        'sport_name': sport_name,
                        'hours': hours,
                        'intensity': intensity
                    })
            
            if not sports_for_calculation:
                return 0
            
            # Chiama la funzione originale dell'agente
            result = calculate_sport_expenditure(sports_for_calculation)
            
            if 'error' in result:
                print(f"[CALORIC_COMPLETER] Errore nel calcolo sport: {result['error']}")
                return 0
                
            return result.get('total_kcal_per_day', 0)
            
        except Exception as e:
            print(f"[CALORIC_COMPLETER] Errore nel calcolo dispendio sportivo: {str(e)}")
            return 0
    
    def _calculate_goal_adjustment(
        self, 
        user_info: Dict[str, Any], 
        bmr: Optional[int]
    ) -> Optional[int]:
        """
        Calcola l'aggiustamento calorico per l'obiettivo dell'utente.
        
        Args:
            user_info: Informazioni di base dell'utente
            bmr: BMR dell'utente (per calcoli percentuali)
            
        Returns:
            Aggiustamento in kcal (positivo per surplus, negativo per deficit)
        """
        try:
            obiettivo = user_info.get('obiettivo', '').lower()
            
            if 'perdita' in obiettivo or 'dimagrimento' in obiettivo or 'dimagrire' in obiettivo:
                # Deficit del 15-20% del BMR (approssimazione conservativa)
                if bmr:
                    return int(-bmr * 0.15)  # -15%
                return -300  # Default conservativo
                
            elif 'aumento' in obiettivo or 'massa' in obiettivo or 'ingrassare' in obiettivo:
                # Surplus del 15-20% del BMR
                if bmr:
                    return int(bmr * 0.15)  # +15%
                return 300  # Default conservativo
                
            else:
                # Mantenimento
                return 0
                
        except Exception as e:
            print(f"[CALORIC_COMPLETER] Errore nel calcolo aggiustamento: {str(e)}")
            return 0
    
    def debug_field_mapping(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utility per debug della mappatura dei campi.
        
        Args:
            extracted_data: Dati estratti da analizzare
            
        Returns:
            Informazioni di debug sulla mappatura
        """
        debug_info = {
            "sections_found": {},
            "caloric_needs_analysis": {}
        }
        
        # Analizza sezioni principali
        for section in ['caloric_needs', 'macros_total', 'meals']:
            found_section = self.field_mapper.find_section_in_data(extracted_data, section)
            if found_section:
                debug_info["sections_found"][section] = found_section
                
                if section == 'caloric_needs':
                    section_data = extracted_data[found_section]
                    debug_info["caloric_needs_analysis"] = self.field_mapper.debug_available_fields(section_data)
        
        return debug_info