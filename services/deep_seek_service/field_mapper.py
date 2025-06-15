"""
Mappatura flessibile dei campi per gestire variazioni nei nomi estratti da DeepSeek.

Questo modulo gestisce il fatto che DeepSeek può estrarre gli stessi concetti 
con nomi diversi (es. 'bmr' vs 'metabolismo_basale' vs 'fabbisogno basale').
"""

import re
from typing import Dict, List, Any, Optional, Union


class FieldMapper:
    """
    Classe per mappare nomi di campi variabili ai nomi standard.
    
    Gestisce:
    - Variazioni di nomenclatura (italiano/inglese)
    - Formato (spazi, underscore, camelCase)
    - Sinonimi e abbreviazioni
    - Case sensitivity
    """
    
    # Mappatura: campo_standard -> lista_di_alias_possibili
    FIELD_MAPPINGS = {
        # Sezione principale
        'caloric_needs': [
            'caloric_needs', 'caloric needs',
            'fabbisogno_calorico', 'fabbisogno calorico', 'fabbisogno-calorico',
            'fabbisogno_energetico', 'fabbisogno energetico', 'fabbisogno-energetico',
            'needs_caloric', 'needs caloric',
            'calorie_needs', 'calorie needs',
            'calorie_fabbisogno', 'calorie fabbisogno',
            'energia', 'energy',
            'calorie', 'calories',
            'kcal_info', 'kcal info',
            'nutrizione_calorica', 'nutrizione calorica'
        ],
        
        # BMR - Metabolismo Basale
        'bmr': [
            'bmr', 'BMR',
            'metabolismo_basale', 'metabolismo basale', 'metabolismo-basale',
            'fabbisogno_basale', 'fabbisogno basale', 'fabbisogno-basale',
            'basale', 'metabolismo', 'metabolism',
            'basal_metabolic_rate', 'basal metabolic rate',
            'tasso_metabolico_basale', 'tasso metabolico basale',
            'dispendio_basale', 'dispendio basale',
            'energia_basale', 'energia basale',
            'calorie_basali', 'calorie basali',
            'kcal_basali', 'kcal basali',
            'base_metabolism', 'base metabolism'
        ],
        
        # LAF - Livello Attività Fisica
        'laf_utilizzato': [
            'laf_utilizzato', 'laf utilizzato', 'laf-utilizzato',
            'laf', 'LAF',
            'livello_attivita', 'livello attivita', 'livello-attivita',
            'livello_attività', 'livello attività', 'livello-attività',
            'activity_level', 'activity level',
            'fattore_attivita', 'fattore attivita', 'fattore-attivita',
            'fattore_attività', 'fattore attività', 'fattore-attività',
            'moltiplicatore_attivita', 'moltiplicatore attivita',
            'moltiplicatore_attività', 'moltiplicatore attività',
            'physical_activity_level', 'physical activity level',
            'activity_factor', 'activity factor'
        ],
        
        # Fabbisogno Base
        'fabbisogno_base': [
            'fabbisogno_base', 'fabbisogno base', 'fabbisogno-base',
            'fabbisogno_giornaliero', 'fabbisogno giornaliero', 'fabbisogno-giornaliero',
            'fabbisogno_quotidiano', 'fabbisogno quotidiano', 'fabbisogno-quotidiano',
            'calorie_giornaliere', 'calorie giornaliere', 'calorie-giornaliere',
            'calorie_quotidiane', 'calorie quotidiane', 'calorie-quotidiane',
            'kcal_giornaliere', 'kcal giornaliere', 'kcal-giornaliere',
            'daily_calories', 'daily calories',
            'daily_needs', 'daily needs',
            'base_needs', 'base needs',
            'energia_giornaliera', 'energia giornaliera',
            'dispendio_giornaliero', 'dispendio giornaliero'
        ],
        
        # Dispendio Sportivo
        'dispendio_sportivo': [
            'dispendio_sportivo', 'dispendio sportivo', 'dispendio-sportivo',
            'calorie_sport', 'calorie sport', 'calorie-sport',
            'kcal_sport', 'kcal sport', 'kcal-sport',
            'sport_calories', 'sport calories',
            'exercise_calories', 'exercise calories',
            'attivita_fisica', 'attivita fisica', 'attivita-fisica',
            'attività_fisica', 'attività fisica', 'attività-fisica',
            'sport_expenditure', 'sport expenditure',
            'exercise_expenditure', 'exercise expenditure',
            'calorie_allenamento', 'calorie allenamento',
            'dispendio_allenamento', 'dispendio allenamento',
            'energia_sport', 'energia sport',
            'consumo_sportivo', 'consumo sportivo'
        ],
        
        # Fabbisogno Totale
        'fabbisogno_finale': [
            'fabbisogno_finale', 'fabbisogno totale', 'fabbisogno-totale',
            'calorie_totali', 'calorie totali', 'calorie-totali',
            'kcal_totali', 'kcal totali', 'kcal-totali',
            'total_calories', 'total calories',
            'total_needs', 'total needs',
            'fabbisogno_complessivo', 'fabbisogno complessivo',
            'calorie_complessive', 'calorie complessive',
            'energia_totale', 'energia totale',
            'dispendio_totale', 'dispendio totale',
            'consumo_totale', 'consumo totale'
        ],
        
        # Aggiustamento Obiettivo
        'aggiustamento_obiettivo': [
            'aggiustamento_obiettivo', 'aggiustamento obiettivo', 'aggiustamento-obiettivo',
            'aggiustamento', 'adjustment',
            'deficit_surplus', 'deficit surplus',
            'deficit_calorico', 'deficit calorico',
            'surplus_calorico', 'surplus calorico',
            'calorie_obiettivo', 'calorie obiettivo',
            'modifica_calorie', 'modifica calorie',
            'correzione_calorie', 'correzione calorie',
            'goal_adjustment', 'goal adjustment',
            'target_adjustment', 'target adjustment',
            'caloric_adjustment', 'caloric adjustment'
        ],
        
        # === MACROS SECTION ===
        
        # Sezione macros
        'macros_total': [
            'macros_total', 'macros total',
            'macronutrienti', 'macronutrients',
            'macros', 'macro',
            'composizione_macronutrienti', 'composizione macronutrienti',
            'ripartizione_macronutrienti', 'ripartizione macronutrienti',
            'daily_macros', 'daily macros',
            'macros_giornalieri', 'macros giornalieri',
            'nutrienti_principali', 'nutrienti principali'
        ],
        
        # Proteine (grammi)
        'proteine': [
            'proteine', 'proteins', 'protein',
            'proteine_g', 'proteine g', 'proteine-g',
            'proteins_g', 'proteins g', 'protein_g',
            'prot', 'prot_g',
            'proteine_grammi', 'proteine grammi',
            'protein_grams', 'protein grams'
        ],
        
        # Carboidrati (grammi)
        'carboidrati': [
            'carboidrati', 'carbohydrates', 'carbs',
            'carboidrati_g', 'carboidrati g', 'carboidrati-g',
            'carbohydrates_g', 'carbs_g', 'carb_g',
            'carbo', 'carbo_g',
            'carboidrati_grammi', 'carboidrati grammi',
            'carbohydrate_grams', 'carb_grams'
        ],
        
        # Grassi (grammi)
        'grassi': [
            'grassi', 'fats', 'fat', 'lipidi', 'lipids',
            'grassi_g', 'grassi g', 'grassi-g',
            'fats_g', 'fat_g', 'lipidi_g',
            'grass', 'grass_g', 'lip_g',
            'grassi_grammi', 'grassi grammi',
            'fat_grams', 'lipid_grams'
        ],
        
        # Proteine (kcal)
        'proteine_kcal': [
            'proteine_kcal', 'proteine kcal', 'proteine-kcal',
            'protein_kcal', 'protein kcal', 'proteins_kcal',
            'proteine_calorie', 'proteine calorie',
            'protein_calories', 'protein calories',
            'kcal_proteine', 'kcal proteine',
            'calorie_proteine', 'calorie proteine',
            'energia_proteine', 'energia proteine'
        ],
        
        # Carboidrati (kcal)
        'carboidrati_kcal': [
            'carboidrati_kcal', 'carboidrati kcal', 'carboidrati-kcal',
            'carbs_kcal', 'carb_kcal', 'carbohydrates_kcal',
            'carboidrati_calorie', 'carboidrati calorie',
            'carb_calories', 'carbohydrate_calories',
            'kcal_carboidrati', 'kcal carboidrati',
            'calorie_carboidrati', 'calorie carboidrati',
            'energia_carboidrati', 'energia carboidrati'
        ],
        
        # Grassi (kcal)
        'grassi_kcal': [
            'grassi_kcal', 'grassi kcal', 'grassi-kcal',
            'fat_kcal', 'fats_kcal', 'lipidi_kcal',
            'grassi_calorie', 'grassi calorie',
            'fat_calories', 'lipid_calories',
            'kcal_grassi', 'kcal grassi',
            'calorie_grassi', 'calorie grassi',
            'energia_grassi', 'energia grassi'
        ],
        
        # Proteine (percentuale)
        'proteine_percentuale': [
            'proteine_percentuale', 'proteine percentuale', 'proteine-percentuale',
            'protein_percentage', 'protein percentage', 'proteins_percentage',
            'proteine_perc', 'proteine perc', 'protein_perc',
            'proteine_%', 'protein_%', 'prot_%',
            'percentuale_proteine', 'percentuale proteine',
            'perc_proteine', 'perc proteine'
        ],
        
        # Carboidrati (percentuale)
        'carboidrati_percentuale': [
            'carboidrati_percentuale', 'carboidrati percentuale', 'carboidrati-percentuale',
            'carbs_percentage', 'carb_percentage', 'carbohydrates_percentage',
            'carboidrati_perc', 'carboidrati perc', 'carbs_perc',
            'carboidrati_%', 'carbs_%', 'carbo_%',
            'percentuale_carboidrati', 'percentuale carboidrati',
            'perc_carboidrati', 'perc carboidrati'
        ],
        
        # Grassi (percentuale)
        'grassi_percentuale': [
            'grassi_percentuale', 'grassi percentuale', 'grassi-percentuale',
            'fat_percentage', 'fats_percentage', 'lipids_percentage',
            'grassi_perc', 'grassi perc', 'fat_perc',
            'grassi_%', 'fat_%', 'lipidi_%',
            'percentuale_grassi', 'percentuale grassi',
            'perc_grassi', 'perc grassi'
        ],
        
        # Kcal totali dai macros
        'kcal_totali_macros': [
            'kcal_totali_macros', 'kcal totali macros', 'kcal-totali-macros',
            'kcal_macros', 'kcal macros', 'kcal-macros',
            'calorie_macros', 'calorie macros', 'calorie-macros',
            'total_kcal_macros', 'total kcal macros',
            'macros_kcal_total', 'macros kcal total',
            'energia_totale_macros', 'energia totale macros',
            'calorie_totali_macros', 'calorie totali macros'
        ],
        
        # === MACROS SECTION ===
        
        # Sezione macros
        'macros_total': [
            'macros_total', 'macros total',
            'macronutrienti', 'macronutrients',
            'macros', 'macro',
            'composizione_macronutrienti', 'composizione macronutrienti',
            'ripartizione_macronutrienti', 'ripartizione macronutrienti',
            'daily_macros', 'daily macros',
            'macros_giornalieri', 'macros giornalieri',
            'nutrienti_principali', 'nutrienti principali'
        ],
        
        # Proteine (grammi)
        'proteine': [
            'proteine', 'proteins', 'protein',
            'proteine_g', 'proteine g', 'proteine-g',
            'proteins_g', 'proteins g', 'protein_g',
            'prot', 'prot_g',
            'proteine_grammi', 'proteine grammi',
            'protein_grams', 'protein grams'
        ],
        
        # Carboidrati (grammi)
        'carboidrati': [
            'carboidrati', 'carbohydrates', 'carbs',
            'carboidrati_g', 'carboidrati g', 'carboidrati-g',
            'carbohydrates_g', 'carbs_g', 'carb_g',
            'carbo', 'carbo_g',
            'carboidrati_grammi', 'carboidrati grammi',
            'carbohydrate_grams', 'carb_grams'
        ],
        
        # Grassi (grammi)
        'grassi': [
            'grassi', 'fats', 'fat', 'lipidi', 'lipids',
            'grassi_g', 'grassi g', 'grassi-g',
            'fats_g', 'fat_g', 'lipidi_g',
            'grass', 'grass_g', 'lip_g',
            'grassi_grammi', 'grassi grammi',
            'fat_grams', 'lipid_grams'
        ],
        
        # Proteine (kcal)
        'proteine_kcal': [
            'proteine_kcal', 'proteine kcal', 'proteine-kcal',
            'protein_kcal', 'protein kcal', 'proteins_kcal',
            'proteine_calorie', 'proteine calorie',
            'protein_calories', 'protein calories',
            'kcal_proteine', 'kcal proteine',
            'calorie_proteine', 'calorie proteine',
            'energia_proteine', 'energia proteine'
        ],
        
        # Carboidrati (kcal)
        'carboidrati_kcal': [
            'carboidrati_kcal', 'carboidrati kcal', 'carboidrati-kcal',
            'carbs_kcal', 'carb_kcal', 'carbohydrates_kcal',
            'carboidrati_calorie', 'carboidrati calorie',
            'carb_calories', 'carbohydrate_calories',
            'kcal_carboidrati', 'kcal carboidrati',
            'calorie_carboidrati', 'calorie carboidrati',
            'energia_carboidrati', 'energia carboidrati'
        ],
        
        # Grassi (kcal)
        'grassi_kcal': [
            'grassi_kcal', 'grassi kcal', 'grassi-kcal',
            'fat_kcal', 'fats_kcal', 'lipidi_kcal',
            'grassi_calorie', 'grassi calorie',
            'fat_calories', 'lipid_calories',
            'kcal_grassi', 'kcal grassi',
            'calorie_grassi', 'calorie grassi',
            'energia_grassi', 'energia grassi'
        ],
        
        # Proteine (percentuale)
        'proteine_percentuale': [
            'proteine_percentuale', 'proteine percentuale', 'proteine-percentuale',
            'protein_percentage', 'protein percentage', 'proteins_percentage',
            'proteine_perc', 'proteine perc', 'protein_perc',
            'proteine_%', 'protein_%', 'prot_%',
            'percentuale_proteine', 'percentuale proteine',
            'perc_proteine', 'perc proteine'
        ],
        
        # Carboidrati (percentuale)
        'carboidrati_percentuale': [
            'carboidrati_percentuale', 'carboidrati percentuale', 'carboidrati-percentuale',
            'carbs_percentage', 'carb_percentage', 'carbohydrates_percentage',
            'carboidrati_perc', 'carboidrati perc', 'carbs_perc',
            'carboidrati_%', 'carbs_%', 'carbo_%',
            'percentuale_carboidrati', 'percentuale carboidrati',
            'perc_carboidrati', 'perc carboidrati'
        ],
        
        # Grassi (percentuale)
        'grassi_percentuale': [
            'grassi_percentuale', 'grassi percentuale', 'grassi-percentuale',
            'fat_percentage', 'fats_percentage', 'lipids_percentage',
            'grassi_perc', 'grassi perc', 'fat_perc',
            'grassi_%', 'fat_%', 'lipidi_%',
            'percentuale_grassi', 'percentuale grassi',
            'perc_grassi', 'perc grassi'
        ],
        
        # Kcal totali dai macros
        'kcal_totali_macros': [
            'kcal_totali_macros', 'kcal totali macros', 'kcal-totali-macros',
            'kcal_macros', 'kcal macros', 'kcal-macros',
            'calorie_macros', 'calorie macros', 'calorie-macros',
            'total_kcal_macros', 'total kcal macros',
            'macros_kcal_total', 'macros kcal total',
            'energia_totale_macros', 'energia totale macros',
            'calorie_totali_macros', 'calorie totali macros'
        ]
    }
    
    @classmethod
    def normalize_key(cls, key: str) -> str:
        """
        Normalizza una chiave per il confronto.
        
        Args:
            key: Chiave da normalizzare
            
        Returns:
            Chiave normalizzata
        """
        if not isinstance(key, str):
            return str(key).lower()
        
        # Converte a lowercase
        normalized = key.lower().strip()
        
        # Sostituisce spazi e trattini con underscore
        normalized = re.sub(r'[-\s]+', '_', normalized)
        
        # Rimuove caratteri speciali
        normalized = re.sub(r'[^\w_]', '', normalized)
        
        # Rimuove underscore multipli
        normalized = re.sub(r'_+', '_', normalized)
        
        # Rimuove underscore iniziali/finali
        normalized = normalized.strip('_')
        
        return normalized
    
    @classmethod
    def find_field_in_data(cls, data: Dict[str, Any], standard_field: str) -> Optional[str]:
        """
        Trova un campo nei dati usando tutte le possibili varianti.
        
        Args:
            data: Dizionario in cui cercare
            standard_field: Nome standard del campo da cercare
            
        Returns:
            Nome del campo trovato nei dati, o None se non trovato
        """
        if not isinstance(data, dict):
            return None
        
        # Prima prova con il nome standard
        if standard_field in data:
            return standard_field
        
        # Ottieni la lista di alias per questo campo
        aliases = cls.FIELD_MAPPINGS.get(standard_field, [])
        
        # Normalizza tutte le chiavi dei dati
        normalized_keys = {cls.normalize_key(k): k for k in data.keys()}
        
        # Cerca tra tutti gli alias
        for alias in aliases:
            normalized_alias = cls.normalize_key(alias)
            if normalized_alias in normalized_keys:
                return normalized_keys[normalized_alias]
        
        return None
    
    @classmethod
    def get_field_value(cls, data: Dict[str, Any], standard_field: str, default: Any = None) -> Any:
        """
        Ottiene il valore di un campo usando tutte le possibili varianti.
        
        Args:
            data: Dizionario da cui estrarre il valore
            standard_field: Nome standard del campo
            default: Valore di default se non trovato
            
        Returns:
            Valore del campo o default se non trovato
        """
        found_key = cls.find_field_in_data(data, standard_field)
        if found_key:
            return data[found_key]
        return default
    
    @classmethod
    def set_field_value(cls, data: Dict[str, Any], standard_field: str, value: Any) -> None:
        """
        Imposta il valore di un campo, usando il nome esistente se presente.
        
        Args:
            data: Dizionario in cui impostare il valore
            standard_field: Nome standard del campo
            value: Valore da impostare
        """
        found_key = cls.find_field_in_data(data, standard_field)
        if found_key:
            # Usa il nome esistente
            data[found_key] = value
        else:
            # Usa il nome standard
            data[standard_field] = value
    
    @classmethod
    def has_field(cls, data: Dict[str, Any], standard_field: str) -> bool:
        """
        Verifica se un campo esiste nei dati (con qualsiasi variante).
        
        Args:
            data: Dizionario in cui cercare
            standard_field: Nome standard del campo
            
        Returns:
            True se il campo esiste, False altrimenti
        """
        return cls.find_field_in_data(data, standard_field) is not None
    
    @classmethod
    def find_section_in_data(cls, data: Dict[str, Any], section_name: str) -> Optional[str]:
        """
        Trova una sezione nei dati usando le varianti possibili.
        
        Args:
            data: Dizionario in cui cercare
            section_name: Nome della sezione da cercare
            
        Returns:
            Nome della sezione trovata, o None se non trovata
        """
        return cls.find_field_in_data(data, section_name)
    
    @classmethod
    def ensure_section_exists(cls, data: Dict[str, Any], section_name: str) -> str:
        """
        Assicura che una sezione esista nei dati, creandola se necessario.
        
        Args:
            data: Dizionario in cui assicurare la sezione
            section_name: Nome standard della sezione
            
        Returns:
            Nome della sezione (esistente o creata)
        """
        found_section = cls.find_section_in_data(data, section_name)
        if found_section:
            return found_section
        
        # Crea la sezione con il nome standard
        data[section_name] = {}
        return section_name
    
    @classmethod
    def get_all_possible_names(cls, standard_field: str) -> List[str]:
        """
        Ottiene tutti i possibili nomi per un campo standard.
        
        Args:
            standard_field: Nome standard del campo
            
        Returns:
            Lista di tutti i possibili nomi/alias
        """
        return cls.FIELD_MAPPINGS.get(standard_field, [standard_field])
    
    @classmethod
    def debug_available_fields(cls, data: Dict[str, Any], section_name: str = None) -> Dict[str, List[str]]:
        """
        Debug utility per vedere quali campi sono disponibili e come mappano.
        
        Args:
            data: Dati da analizzare
            section_name: Nome della sezione da analizzare (opzionale)
            
        Returns:
            Dizionario con info di mappatura
        """
        target_data = data
        if section_name:
            section_key = cls.find_section_in_data(data, section_name)
            if section_key:
                target_data = data[section_key]
            else:
                return {"error": f"Sezione {section_name} non trovata"}
        
        result = {
            "available_keys": list(target_data.keys()),
            "mapped_fields": {},
            "unmapped_keys": []
        }
        
        # Trova quali campi standard mappano
        for standard_field in cls.FIELD_MAPPINGS.keys():
            found_key = cls.find_field_in_data(target_data, standard_field)
            if found_key:
                result["mapped_fields"][standard_field] = found_key
        
        # Trova chiavi non mappate
        mapped_keys = set(result["mapped_fields"].values())
        result["unmapped_keys"] = [k for k in target_data.keys() if k not in mapped_keys]
        
        return result


# Istanza globale per facilità d'uso
field_mapper = FieldMapper()

# Funzioni di convenienza
def find_field(data: Dict[str, Any], field: str) -> Optional[str]:
    """Trova un campo nei dati."""
    return field_mapper.find_field_in_data(data, field)

def get_field(data: Dict[str, Any], field: str, default: Any = None) -> Any:
    """Ottiene il valore di un campo."""
    return field_mapper.get_field_value(data, field, default)

def set_field(data: Dict[str, Any], field: str, value: Any) -> None:
    """Imposta il valore di un campo."""
    field_mapper.set_field_value(data, field, value)

def has_field(data: Dict[str, Any], field: str) -> bool:
    """Verifica se un campo esiste."""
    return field_mapper.has_field(data, field)

def ensure_section(data: Dict[str, Any], section: str) -> str:
    """Assicura che una sezione esista."""
    return field_mapper.ensure_section_exists(data, section)