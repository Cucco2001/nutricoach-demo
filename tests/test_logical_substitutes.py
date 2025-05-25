#!/usr/bin/env python3
"""
Test per verificare i sostituti logici
"""

from nutridb_tool import get_food_substitutes

def test_logical_substitutes():
    """Test dei sostituti logici"""
    
    print("🧪 TEST SOSTITUTI LOGICI")
    print("=" * 60)
    
    # Test casi problematici precedenti
    test_cases = [
        ("pasta_secca", 80, "Pasta secca - dovrebbe avere cereali simili"),
        ("riso", 60, "Riso - dovrebbe avere cereali simili"),
        ("pollo_petto", 150, "Pollo petto - dovrebbe avere proteine animali"),
        ("melanzane", 200, "Melanzane - dovrebbe avere verdure simili"),
        ("arancia", 150, "Arancia - dovrebbe avere frutta simile"),
        ("olio_oliva", 10, "Olio oliva - dovrebbe avere grassi simili"),
        ("latte_intero", 250, "Latte - dovrebbe avere latticini simili")
    ]
    
    for food, grams, description in test_cases:
        print(f"\n📋 {description}")
        print("-" * 50)
        
        result = get_food_substitutes(food, grams, 5)
        
        if "error" in result:
            print(f"❌ Errore: {result['error']}")
            continue
        
        if not result.get("available", False):
            print(f"⚠️ Sistema non disponibile")
            continue
        
        # Mostra alimento di riferimento
        ref = result["reference_food"]
        print(f"🍽️ Alimento: {ref['name']} ({ref['grams']}g)")
        print(f"🔥 Calorie: {ref['nutrition']['energia_kcal']} kcal")
        
        # Mostra sostituti
        print(f"\n🔄 Sostituti trovati:")
        for i, sub in enumerate(result['substitutes'], 1):
            print(f"  {i}. {sub['name']}: {sub['equivalent_grams']}g")
            print(f"     🎯 Similarità: {sub['similarity_score']:.1f}%")
            print(f"     🔥 Calorie: {sub['equivalent_nutrition']['energia_kcal']} kcal")
            
            # Valuta la logica del sostituto
            is_logical = evaluate_substitution_logic(food, sub['name'])
            if is_logical:
                print(f"     ✅ Sostituzione logica")
            else:
                print(f"     ⚠️ Sostituzione questionabile")
    
    print(f"\n🎉 Test completato!")

def evaluate_substitution_logic(original: str, substitute: str) -> bool:
    """Valuta se una sostituzione è logica"""
    
    # Definisci gruppi logici
    logical_groups = {
        "cereali": ["pasta_secca", "pasta_integrale", "riso", "riso_integrale", "riso_basmati", "avena", "cornflakes"],
        "pane": ["pane_bianco", "crostata_di_marmellata"],
        "carni": ["pollo", "pollo_petto", "pollo_coscia", "pollo_ali"],
        "pesci": ["tonno_naturale", "tonno_sottolio_sgocciolato", "salmone_al_naturale", "salmone_affumicato", "pesce_spada"],
        "salumi": ["bresaola", "prosciutto_crudo"],
        "proteine": ["iso_fuji_yamamoto", "pro_milk_20g_proteine"],
        "latte": ["latte_intero", "latte_scremato"],
        "yogurt": ["yogurt_greco_0percento", "yogurt_greco_2percento", "yogurt_magro"],
        "gelati": ["gelato_cioccolato", "gelato_fiordilatte"],
        "uova": ["uovo", "uova", "albume_uova"],
        "grassi": ["olio_oliva", "burro", "margarina"],
        "frutta_secca": ["noci_sgusciate", "mandorle", "burro_arachidi"],
        "verdure": ["verdure_miste", "spinaci_cotti", "zucchine", "melanzane", "carote_crude"],
        "frutta": ["mela", "pera", "banana", "uva", "arancia", "albicocche", "frutti_di_bosco"]
    }
    
    # Trova i gruppi di appartenenza
    original_groups = []
    substitute_groups = []
    
    for group_name, foods in logical_groups.items():
        if original in foods:
            original_groups.append(group_name)
        if substitute in foods:
            substitute_groups.append(group_name)
    
    # Verifica se appartengono allo stesso gruppo o a gruppi correlati
    if any(group in substitute_groups for group in original_groups):
        return True
    
    # Gruppi correlati
    related_groups = [
        ["cereali", "pane"],  # Carboidrati complessi
        ["carni", "pesci", "salumi", "proteine"],  # Proteine
        ["latte", "yogurt"],  # Latticini
        ["grassi", "frutta_secca"],  # Grassi
    ]
    
    for related in related_groups:
        original_in_related = any(group in related for group in original_groups)
        substitute_in_related = any(group in related for group in substitute_groups)
        if original_in_related and substitute_in_related:
            return True
    
    return False

if __name__ == "__main__":
    test_logical_substitutes() 