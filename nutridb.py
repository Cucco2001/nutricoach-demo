import json
import os


class NutriDB:
    def __init__(self, path):
        self.alimenti = self._load_json(os.path.join(path, "banca_alimenti_crea_60alimenti.json"))
        self.conversioni = self._load_json(os.path.join(path, "fattori_conversione_cottura.json"))
        self.larn_proteine = self._load_json(os.path.join(path, "larn_proteine.json"))["proteine"]
        self.larn_energy_18_60 = self._load_json(os.path.join(path, "larn_energy_18-60_anni.json"))
        self.larn_fibre_carboidrati = self._load_json(os.path.join(path, "larn_carboidrati_e_fibre.json"))
        self.larn_lipidi = self._load_json(os.path.join(path, "larn_lipidi.json"))["lipidi"]
        self.larn_vitamine = self._load_json(os.path.join(path, "larn_vitamine.json"))["vitamine"]
        self.porzioni = self._load_json(os.path.join(path, "porzioni_standard.json"))
        self.peso_volume = self._load_json(os.path.join(path, "peso_per_volume.json"))
        self.alias = self._build_alias()

    def _load_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_alias(self):
        mapping = {}
        for key in self.alimenti:
            clean = key.lower().replace("_", " ")
            mapping[clean] = key
        mapping.update({
            "pollo": "pollo", "riso": "riso", "pasta": "pasta_secca",
            "tonno": "tonno_naturale", "yogurt greco": "yogurt_greco_0percento",
            "iso": "iso_fuji_yamamoto", "burro arachidi": "burro_ara_chidi"
        })
        return mapping

    def get_macros(self, alimento, quantità=100):
        key = self.alias.get(alimento.lower().replace("_", " "))
        if not key:
            raise ValueError(f"Alimento '{alimento}' non trovato.")
        info = self.alimenti[key]
        factor = quantità / 100
        return {k: round(v * factor, 2) for k, v in info.items()}

    def get_LARN_protein(self, sesso, età, peso):
        sesso = sesso.lower()
        if età < 18:
            raise NotImplementedError("Supporto per età <18 non implementato.")
        if sesso == "maschio":
            key = "maschi_18_29_anni" if età < 30 else "maschi_30_59_anni"
        else:
            key = "femmine_18_29_anni" if età < 30 else "femmine_30_59_anni"
        entry = self.larn_proteine["adulti"][key]
        g_kg = entry["PRI"]["g_kg"]
        return round(g_kg * peso, 2)

    def get_LARN_energy(self, sesso, età, altezza, LAF):
        sesso = sesso.lower()
        group = "maschi_18_29" if sesso == "maschio" and età < 30 else \
                "maschi_30_59" if sesso == "maschio" else \
                "femmine_18_29" if età < 30 else "femmine_30_59"
        altezza = str(round(float(altezza), 2))[:4]
        if altezza not in self.larn_energy_18_60[group]:
            raise ValueError("Altezza non trovata nei dati LARN.")
        return self.larn_energy_18_60[group][altezza][f"LAF_{LAF}"]

    def get_standard_portion(self, categoria, sottocategoria):
        if categoria in self.porzioni:
            if sottocategoria in self.porzioni[categoria]:
                dati = self.porzioni[categoria][sottocategoria]
                return dati["quantità"], dati["unità"], dati.get("esempi", [])
        raise ValueError("Categoria o sottocategoria non trovata.")

    def get_weight_from_volume(self, alimento, tipo_misura):
        alimento = alimento.lower().replace(" ", "_")
        if alimento in self.peso_volume and tipo_misura in self.peso_volume[alimento]:
            return self.peso_volume[alimento][tipo_misura]
        raise ValueError(f"Nessun dato volume/peso per {alimento}, misura: {tipo_misura}")

    def get_fattore_cottura(self, categoria, metodo_cottura, sotto_categoria):
        """Esempio: ('cereali_e_tuberi', 'bollitura', 'riso_basmati')"""
        try:
            return self.conversioni[categoria][metodo_cottura][sotto_categoria]["fattore"]
        except KeyError:
            raise ValueError(f"Nessun fattore di cottura trovato per {categoria} - {metodo_cottura} - {sotto_categoria}")

    def get_LARN_fibre(self, kcal):
        """Restituisce il range consigliato di fibra in grammi, in base alle kcal"""
        ai_str = self.larn_fibre_carboidrati["fibra_alimentare"]["AI"]["adulti"]
        min_g_per_kcal = float(ai_str.split("–")[0])
        max_g_per_kcal = float(ai_str.split("–")[1].split()[0])
        return round(kcal * min_g_per_kcal / 1000), round(kcal * max_g_per_kcal / 1000)

    def get_LARN_carboidrati_percentuali(self):
        """Restituisce il range % En dei carboidrati"""
        ri = self.larn_fibre_carboidrati["carboidrati"]["RI"]
        return ri

    def get_LARN_lipidi_percentuali(self):
        """Restituisce il range % En consigliato per i grassi"""
        return self.larn_lipidi["adulti_anziani"]["lipidi_totali"]

    def get_LARN_vitamine(self, sesso, età):
        """Restituisce fabbisogno vitaminico per adulti 18-59"""
        sesso = sesso.lower()
        if sesso == "maschio":
            return self.larn_vitamine["maschi_18_29"] if età < 30 else self.larn_vitamine["maschi_30_59"]
        else:
            return self.larn_vitamine["femmine_18_29"] if età < 30 else self.larn_vitamine["femmine_30_59"]
