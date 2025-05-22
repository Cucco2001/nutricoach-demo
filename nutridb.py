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
        """Costruisce un dizionario di alias per i nomi degli alimenti.
        
        Questa è una funzione interna usata solo dalla classe NutriDB durante l'inizializzazione.
        Crea un mapping tra nomi comuni/alternativi degli alimenti e le loro chiavi nel database.
        
        Non dovrebbe essere chiamata direttamente - viene invocata automaticamente dal costruttore
        di NutriDB per popolare l'attributo self.alias.
        
        Returns:
            Dict[str, str]: Mapping tra alias (chiave) e nome canonico (valore) dell'alimento
        """
        mapping = {}
        for key in self.alimenti:
            clean = key.lower().replace("_", " ")
            mapping[clean] = key
        mapping.update({
            "pollo": "pollo",
            "petto di pollo": "pollo_petto", 
            "petto pollo": "pollo_petto",
            "coscia di pollo": "pollo_coscia",
            "coscia pollo": "pollo_coscia", 
            "ali di pollo": "pollo_ali",
            "ali pollo": "pollo_ali",
            "riso normale": "riso",
            "riso basmati": "riso_basmati",
            "basmati riso": "riso_basmati",
            "riso integrale": "riso_integrale",
            "integrale riso": "riso_integrale",     
            "pasta": "pasta_secca",
            "pasta secca": "pasta_secca",
            "tonno": "tonno_naturale",
            "tonno naturale": "tonno_naturale",
            "yogurt greco": "yogurt_greco_0percento",
            "yogurt greco 0%": "yogurt_greco_0percento",
            "yogurt greco 0 percento": "yogurt_greco_0percento",
            "yogurt greco 2%": "yogurt_greco_2percento",
            "yogurt greco 2 percento": "yogurt_greco_2percento",
            "iso": "iso_fuji_yamamoto",
            "pro milk 20g": "pro_milk_20g_proteine",
            "pro milk": "pro_milk_20g_proteine",  
            "iso fuji yamamoto": "iso_fuji_yamamoto",
            "burro arachidi": "burro_arachidi",
            "latte scremato": "latte_scremato",
            "latte": "latte_intero",
            "latte parzialmente scremato": "latte_scremato",
            "latte intero": "latte_intero"
        })
        return mapping

    def get_macros(self, alimento, quantità=100):
        key = self.alias.get(alimento.lower().replace("_", " "))
        if not key:
            raise ValueError(f"Alimento '{alimento}' non trovato.")
        info = self.alimenti[key]
        factor = quantità / 100
        return {k: round(v * factor, 2) for k, v in info.items()}

    def get_LARN_protein(self, sesso, età):
        """Calcola il fabbisogno proteico in g/kg usando i LARN.
        
        Args:
            sesso: 'maschio' o 'femmina'
            età: età in anni
        
        Returns:
            grammi di proteine per kg di peso corporeo (g/kg)
        
        Raises:
            NotImplementedError: se età <18 anni
        """
        sesso = sesso.lower()
        if età < 18:
            raise NotImplementedError("Supporto per età <18 non implementato.")
        if sesso == "maschio":
            key = "maschi_18_29_anni" if età < 30 else "maschi_30_59_anni"
        else:
            key = "femmine_18_29_anni" if età < 30 else "femmine_30_59_anni"
        entry = self.larn_proteine["adulti"][key]
        g_kg = entry["PRI"]["g_kg"]
        return g_kg

    def get_LARN_energy(self, sesso, età, altezza, LAF):
        """Calcola il fabbisogno energetico usando i LARN.
        
        Args:
            sesso: 'maschio' o 'femmina'
            età: età in anni
            altezza: altezza in cm
            LAF: livello di attività fisica (1.45, 1.60, 1.75, or 2.10)
        
        Returns:
            fabbisogno energetico in kcal
        
        Raises:
            ValueError: se i parametri non sono validi
        """
        # Validazione parametri
        sesso = str(sesso).lower()
        if sesso not in ["maschio", "femmina"]:
            raise ValueError("Sesso deve essere 'maschio' o 'femmina'")
            
        try:
            età = int(float(età))  # Gestisce sia stringhe che float
            if età < 18 or età >= 60:
                raise ValueError("L'età deve essere compresa tra 18 e 59 anni")
        except (ValueError, TypeError):
            raise ValueError("Età deve essere un numero intero tra 18 e 59")
            
        try:
            altezza = float(altezza)
            if altezza < 140 or altezza > 220:
                raise ValueError("L'altezza deve essere compresa tra 140 e 220 cm")
        except (ValueError, TypeError):
            raise ValueError("Altezza deve essere un numero tra 140 e 220")

        # Validazione e conversione LAF
        valid_lafs = [1.45, 1.60, 1.75, 2.10]
        try:
            LAF = float(str(LAF).replace(",", "."))  # Gestisce anche valori con la virgola
            if LAF not in valid_lafs:
                closest_laf = min(valid_lafs, key=lambda x: abs(x - LAF))
                print(f"ATTENZIONE: LAF {LAF} convertito al valore valido più vicino: {closest_laf}")
                LAF = closest_laf
        except (ValueError, TypeError):
            raise ValueError("LAF deve essere uno dei seguenti valori: 1.45, 1.60, 1.75, 2.10")

        # Determina il gruppo di età/sesso
        group = "maschi_18_29" if sesso == "maschio" and età < 30 else \
                "maschi_30_59" if sesso == "maschio" else \
                "femmine_18_29" if età < 30 else "femmine_30_59"
        
        # Converti altezza da cm a m e formatta con due decimali
        altezza_m = f"{altezza/100:.2f}"  # Converte in stringa con 2 decimali
        
        try:
            # Trova i valori di altezza disponibili
            altezze = sorted([str(h) for h in self.larn_energy_18_60[group].keys()])
            
            # Se l'altezza corrisponde esattamente a un valore disponibile
            if altezza_m in altezze:
                energia = self.larn_energy_18_60[group][altezza_m][f"LAF_{LAF}"]
                return round(float(energia))
            
            # Altrimenti, trova i valori più vicini per l'interpolazione
            altezze_float = [float(h) for h in altezze]
            altezza_m_float = float(altezza_m)
            
            # Gestione casi limite
            if altezza_m_float <= altezze_float[0]:
                energia = self.larn_energy_18_60[group][altezze[0]][f"LAF_{LAF}"]
                return round(float(energia))
            if altezza_m_float >= altezze_float[-1]:
                energia = self.larn_energy_18_60[group][altezze[-1]][f"LAF_{LAF}"]
                return round(float(energia))
            
            # Trova i valori di altezza per l'interpolazione
            for i, h in enumerate(altezze_float):
                if h >= altezza_m_float:
                    h1, h2 = altezze[i-1], altezze[i]
                    break
            
            # Recupera i valori energetici
            try:
                e1 = float(self.larn_energy_18_60[group][h1][f"LAF_{LAF}"])
                e2 = float(self.larn_energy_18_60[group][h2][f"LAF_{LAF}"])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Errore nei dati LARN per LAF_{LAF}: {str(e)}")
            
            # Interpolazione lineare
            h1_float, h2_float = float(h1), float(h2)
            energia = e1 + (altezza_m_float - h1_float) * (e2 - e1) / (h2_float - h1_float)
            
            return round(float(energia))
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Errore nel recupero dei dati LARN: {str(e)}")
        except Exception as e:
            raise ValueError(f"Errore imprevisto nel calcolo: {str(e)}")

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
        """Restituisce il range consigliato di fibra in grammi, in base alle kcal
        
        Args:
            kcal: fabbisogno energetico giornaliero in kcal
            
        Returns:
            tuple: (min_g, max_g) range di grammi di fibra consigliati
            
        Raises:
            ValueError: se i parametri non sono validi
        """
        try:
            kcal = float(kcal)
            if kcal <= 0:
                raise ValueError("Il fabbisogno energetico deve essere positivo")
            if kcal < 800 or kcal > 4000:
                raise ValueError("Il fabbisogno energetico deve essere tra 800 e 4000 kcal")
        except (ValueError, TypeError):
            raise ValueError("kcal deve essere un numero positivo")

        try:
            # Recupera il valore AI per la fibra
            ai_str = self.larn_fibre_carboidrati["fibra_alimentare"]["AI"]["adulti"]
            
            # Estrai la parte relativa a kcal (prima delle parentesi)
            kcal_part = ai_str.split("(")[0].strip()
            
            # Estrai i valori numerici (prima di g/1000 kcal)
            range_part = kcal_part.split("g/1000")[0].strip()
            
            # Gestisci diversi tipi di trattini
            range_part = range_part.replace("–", "-").replace("—", "-")
            
            # Estrai i valori min e max
            parts = range_part.split("-")
            if len(parts) != 2:
                raise ValueError(f"Formato AI non valido: {ai_str}")
            
            try:
                min_g_per_kcal = float(parts[0])
                max_g_per_kcal = float(parts[1])
            except (ValueError, IndexError):
                raise ValueError(f"Impossibile estrarre i valori numerici da: {range_part}")
            
            # Calcola il range di fibra
            min_g = round(kcal * min_g_per_kcal / 1000, 1)
            max_g = round(kcal * max_g_per_kcal / 1000, 1)
            
            # Applica il minimo assoluto di 25g come specificato nelle note
            min_g = max(25.0, min_g) if kcal < 2000 else min_g
            
            # Verifica che i risultati siano sensati
            if min_g <= 0 or max_g <= 0 or min_g > max_g:
                raise ValueError(f"Valori calcolati non validi: min={min_g}, max={max_g}")
            
            return min_g, max_g
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Errore nel recupero dei dati LARN per la fibra: {str(e)}")
        except Exception as e:
            raise ValueError(f"Errore nel calcolo della fibra: {str(e)}")

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

    def check_ultraprocessed_foods(self, foods_with_grams):
        """Verifica se una dieta giornaliera contiene troppi alimenti ultra-processati (NOVA classe 4).
        
        Args:
            foods_with_grams: Un dizionario dove le chiavi sono i nomi degli alimenti e i valori sono i grammi.
            
        Returns:
            Un dizionario contenente:
            - 'too_much_ultraprocessed': True se più del 20% della dieta è composta da alimenti ultraprocessati, False altrimenti
            - 'ultraprocessed_ratio': Rapporto tra grammi di alimenti ultraprocessati e grammi totali
            - 'ultraprocessed_grams': Grammi totali di alimenti ultraprocessati
            - 'total_grams': Grammi totali di tutti gli alimenti
        """
        ultraprocessed_grams = 0
        total_grams = 0
        ultraprocessed_foods = []
        unrecognized_foods = []
        
        for food, grams in foods_with_grams.items():
            total_grams += grams
            
            try:
                # Cerca l'alimento nella banca dati usando gli alias
                key = self.alias.get(food.lower().replace("_", " "))
                if not key:
                    unrecognized_foods.append(food)
                    continue
                
                # Controlla il gruppo NOVA dell'alimento
                if self.alimenti[key].get("nova_group") == 4:
                    ultraprocessed_grams += grams
                    ultraprocessed_foods.append(food)
            except Exception as e:
                unrecognized_foods.append(food)
        
        ultraprocessed_ratio = 0
        if total_grams > 0:
            ultraprocessed_ratio = ultraprocessed_grams / total_grams
        
        result = {
            "too_much_ultraprocessed": ultraprocessed_ratio > 0.2,  # True se supera il 20%
            "ultraprocessed_ratio": round(ultraprocessed_ratio, 3),
            "ultraprocessed_grams": ultraprocessed_grams,
            "total_grams": total_grams,
            "ultraprocessed_foods": ultraprocessed_foods
        }
        
        if unrecognized_foods:
            result["unrecognized_foods"] = unrecognized_foods
            
        return result
