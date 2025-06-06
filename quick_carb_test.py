import json

# Carica database
db = json.load(open('Dati_processed/banca_alimenti_crea_60alimenti.json', 'r', encoding='utf-8'))

foods = ['patate', 'broccoli', 'olio_oliva']

print("🧪 MASSIMI CARBOIDRATI POSSIBILI:")
print("=" * 40)

total_max_carbs = 0

for food in foods:
    carb_per_100g = db[food]['carboidrati_g']
    
    # Vincoli di porzione per categoria
    if food == 'patate':  # tuberi: 80-500g
        max_g = 500
    elif food == 'broccoli':  # verdure: 50-400g
        max_g = 400
    elif food == 'olio_oliva':  # grassi_aggiunti: 5-30g
        max_g = 30
    
    max_carbs = carb_per_100g * max_g / 100
    total_max_carbs += max_carbs
    
    print(f"• {food}: {carb_per_100g}g/100g → max {max_carbs:.1f}g (a {max_g}g)")

print()
print(f"🎯 TOTALE MASSIMO: {total_max_carbs:.1f}g")
print(f"🎯 TARGET RICHIESTO: 78g")

if total_max_carbs < 78:
    deficit = 78 - total_max_carbs
    print(f"❌ DEFICIT: {deficit:.1f}g carboidrati IMPOSSIBILI da raggiungere!")
    print(f"📊 Percentuale raggiungibile: {(total_max_carbs/78*100):.1f}%")
    print("\n💡 CONCLUSIONE:")
    print("   🚨 È FISICAMENTE IMPOSSIBILE raggiungere 78g di carboidrati")
    print("   🔄 Serve AGGIUNGERE alimenti ricchi di carboidrati!")
    print("   💡 Suggerimenti: pasta, riso, pane, cereali, legumi")
else:
    surplus = total_max_carbs - 78
    print(f"✅ SURPLUS: {surplus:.1f}g carboidrati extra disponibili")
    print("\n💡 CONCLUSIONE:")
    print("   ✅ I target sono teoricamente raggiungibili")
    print("   🤔 Il problema è nell'algoritmo di ottimizzazione") 