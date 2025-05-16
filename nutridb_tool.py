from nutridb import NutriDB

db = NutriDB("Dati_processed")  # Sostituisci con il path corretto

def nutridb_tool(function_name: str, parameters: dict) -> dict:
    """Tool principale per accedere alle funzioni del database nutrizionale."""

    if function_name == "get_macros":
        return db.get_macros(parameters["alimento"], parameters.get("quantità", 100))

    elif function_name == "get_LARN_protein":
        return {"g_proteine": db.get_LARN_protein(
            parameters["sesso"], parameters["età"], parameters["peso"])}

    elif function_name == "get_LARN_energy":
        return {"kcal": db.get_LARN_energy(
            parameters["sesso"], parameters["età"], parameters["altezza"], parameters["LAF"])}

    elif function_name == "get_standard_portion":
        quantità, unità, esempi = db.get_standard_portion(
            parameters["categoria"], parameters["sottocategoria"])
        return {"quantità": quantità, "unità": unità, "esempi": esempi}

    elif function_name == "get_weight_from_volume":
        return {"peso_g": db.get_weight_from_volume(
            parameters["alimento"], parameters["tipo_misura"])}

    elif function_name == "get_fattore_cottura":
        return {"fattore": db.get_fattore_cottura(
            parameters["categoria"], parameters["metodo_cottura"], parameters["sotto_categoria"])}

    elif function_name == "get_LARN_fibre":
        fibra_min, fibra_max = db.get_LARN_fibre(parameters["kcal"])
        return {"fibra_min": fibra_min, "fibra_max": fibra_max}

    elif function_name == "get_LARN_carboidrati_percentuali":
        return {"range_percentuale": db.get_LARN_carboidrati_percentuali()}

    elif function_name == "get_LARN_lipidi_percentuali":
        return {"range_percentuale": db.get_LARN_lipidi_percentuali()}

    elif function_name == "get_LARN_vitamine":
        return db.get_LARN_vitamine(parameters["sesso"], parameters["età"])

    else:
        raise ValueError(f"Funzione '{function_name}' non supportata.")