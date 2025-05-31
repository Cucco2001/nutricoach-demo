#!/usr/bin/env python3
"""
Test per la funzione check_vitamins
"""

from agent_tools.nutridb_tool import check_vitamins

def test_check_vitamins():
    """Test della funzione check_vitamins"""
    
    print("=== TEST CONTROLLO VITAMINICO ===")
    
    # Dieta di esempio con vari alimenti
    foods_with_grams = {
        "pasta_secca": 80,
        "pollo_petto": 150,
        "zucchine": 200,
        "olio_oliva": 15,
        "mela": 150,
        "uovo": 60,
        "latte_intero": 250,
        "fagioli_borlotti_cotti": 100
    }
    
    # Test per uomo adulto
    result = check_vitamins(foods_with_grams, "maschio", 30)
    
    print("Risultato controllo vitaminico:")
    print(f"- Totali vitaminici: {result.get('total_vitamins', {})}")
    print(f"- Fabbisogni LARN: {result.get('larn_requirements', {})}")
    print(f"- Stato vitamine: {result.get('vitamin_status', {})}")
    print(f"- Avvertimenti: {result.get('warnings', [])}")
    print(f"- Raccomandazioni: {result.get('recommendations', [])}")
    
    # Verifica che non ci siano errori
    if "error" in result:
        print(f"❌ ERRORE: {result['error']}")
        return False
    
    # Verifica che ci siano i dati attesi
    if "total_vitamins" not in result:
        print("❌ ERRORE: Mancano i totali vitaminici")
        return False
    
    if "vitamin_status" not in result:
        print("❌ ERRORE: Manca lo stato delle vitamine")
        return False
    
    print("✅ Test completato con successo!")
    
    # Mostra alcuni dettagli interessanti
    print("\n📊 Dettagli vitamine:")
    for vitamin, status in result.get('vitamin_status', {}).items():
        print(f"- {vitamin}: {status['amount']:.2f} ({status['percentage']:.1f}% del fabbisogno) - {status['status']}")
    
    return True

if __name__ == "__main__":
    test_check_vitamins() 