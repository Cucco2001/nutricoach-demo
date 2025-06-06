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
        self.data_dir = path
        
        # Carica il database dei sostituti se disponibile
        try:
            self.substitutes = self._load_json(os.path.join(path, "alimenti_sostitutivi.json"))
        except FileNotFoundError:
            self.substitutes = None

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
            "riso bianco": "riso",
            "basmati riso": "riso_basmati",
            "riso integrale": "riso_integrale",
            "fiocchi di riso": "riso",
            "fiocchi di avena": "avena",
            "fiocchi d'avena": "avena",
            "pecorino": "parmigiano_reggiano",
            "parmigiano reggiano": "parmigiano_reggiano",
            "parmigiano": "parmigiano_reggiano",    
            "formaggio parmigiano": "parmigiano_reggiano",
            "formaggio": "parmigiano_reggiano",
            "mozzarella": "parmigiano_reggiano",
            "mozzarella di bufala": "parmigiano_reggiano",
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
            "proteine in polvere": "iso_fuji_yamamoto",
            "proteine": "iso_fuji_yamamoto",
            "proteine del siero del latte": "iso_fuji_yamamoto",
            "proteine del latte": "iso_fuji_yamamoto",
            "proteine del latte di mandorle": "iso_fuji_yamamoto",
            "iso": "iso_fuji_yamamoto",
            "pro milk 20g": "pro_milk_20g_proteine",
            "pro milk": "pro_milk_20g_proteine",  
            "iso fuji yamamoto": "iso_fuji_yamamoto",
            "burro arachidi": "burro_arachidi",
            "cereali integrali": "cornflakes",
            "burro di arachidi": "burro_arachidi",
            "verdure miste": "verdure_miste",
            "verdure": "verdure_miste",
            "pomodori": "verdure_miste",
            "pomodori secchi": "verdure_miste",
            "pomodoro": "verdure_miste",
            "verdura": "verdure_miste",
            "latte scremato": "latte_scremato",
            "latte": "latte_intero",
            "latte parzialmente scremato": "latte_scremato",
            "latte intero": "latte_intero",
            "crostata di marmellata": "crostata_di_marmellata",
            "crostata marmellata": "crostata_di_marmellata",
            "crostata": "crostata_di_marmellata",
            "marmellata": "crostata_di_marmellata",
            "crostata alla marmellata": "crostata_di_marmellata",
            "noci sgusciate": "noci_sgusciate",
            "noci": "noci_sgusciate",
            "mandorle tostate": "mandorle",
            "frutti di bosco": "frutti_di_bosco",
            "albume uova": "albume_uova",
            "albume": "albume_uova",
            "albume d'uovo": "albume_uova",
            "albume d'uova": "albume_uova",
            "albume d'uova fresco": "albume_uova",
            "albume d'uova fresco": "albume_uova",
            "biscotti secchi": "biscotti_secchi",
            "biscotti": "biscotti_secchi",
            "frollini": "biscotti_secchi",
            "biscotti integrali": "biscotti_integrali",
            "patata": "patate",
            "patate dolci": "patate",
            "salmone": "salmone_affumicato",
            "tonno": "tonno_naturale",
            "olio di oliva": "olio_oliva",
            "olio": "olio_oliva",
            "olio extravergine": "olio_oliva",
            "olio extravergine di oliva": "olio_oliva",
            "olio extravergine di oliva": "olio_oliva",
            "olio d'oliva": "olio_oliva",
            "olio di semi": "olio_oliva",
            "pane": "pane_bianco",
            "pane integrale": "pane_bianco",
            "pane bianco": "pane_bianco",
            "pane al latte": "pane_bianco",
            "pan bauletto": "pane_bianco",
            "pane fresco": "pane_bianco"
            })
        return mapping

    def get_macros(self, alimento, quantità=100):
        key = self.alias.get(alimento.lower().replace("_", " "))
        if not key:
            raise ValueError(f"Alimento '{alimento}' non trovato.")
        info = self.alimenti[key]
        factor = quantità / 100
        
        # Filtra solo i valori numerici e gestisce anche i valori stringa che rappresentano numeri
        result = {}
        for k, v in info.items():
            if isinstance(v, (int, float)):
                result[k] = round(v * factor, 2)
            elif isinstance(v, str):
                # Prova a convertire stringhe che rappresentano numeri
                try:
                    numeric_value = float(v)
                    result[k] = round(numeric_value * factor, 2)
                except ValueError:
                    # Se non è convertibile, mantieni la stringa originale
                    result[k] = v
            else:
                # Per altri tipi (liste, dict, etc.) mantieni il valore originale
                result[k] = v
        
        return result

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
            LAF: livello di attività fisica (1.30, 1.45, 1.60, or 1.75)
        
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
        valid_lafs = [1.30, 1.45, 1.60, 1.75]
        try:
            LAF = float(str(LAF).replace(",", "."))  # Gestisce anche valori con la virgola
            if LAF not in valid_lafs:
                closest_laf = min(valid_lafs, key=lambda x: abs(x - LAF))
                print(f"ATTENZIONE: LAF {LAF} convertito al valore valido più vicino: {closest_laf}")
                LAF = closest_laf
        except (ValueError, TypeError):
            raise ValueError("LAF deve essere uno dei seguenti valori: 1.30, 1.45, 1.60, 1.75")

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

    def calculate_weight_goal_calories(self, kg_change, time_months, goal_type, bmr=None):
        """Calcola il deficit o surplus calorico giornaliero per raggiungere l'obiettivo di peso.
        
        Args:
            kg_change: Numero di kg da cambiare (sempre positivo)
            time_months: Tempo in mesi per raggiungere l'obiettivo
            goal_type: "perdita_peso" o "aumento_massa"
            bmr: Metabolismo basale in kcal (opzionale, per verifica deficit)
        
        Returns:
            dict: Contiene:
                - daily_calorie_adjustment: deficit/surplus calorico giornaliero (negativo per deficit, positivo per surplus)
                - warnings: lista di avvertimenti se applicabile
                - goal_type: tipo di obiettivo confermato
                - kg_per_month: velocità di cambiamento
        
        Raises:
            ValueError: se i parametri non sono validi
        """
        # Validazione parametri
        try:
            kg_change = float(kg_change)
            time_months = float(time_months)
            if bmr is not None:
                bmr = float(bmr)
        except (ValueError, TypeError):
            raise ValueError("I parametri kg_change e time_months devono essere numerici")
        
        if kg_change <= 0:
            raise ValueError("I kg da cambiare devono essere positivi")
        
        if time_months <= 0:
            raise ValueError("Il tempo deve essere positivo")
        
        if goal_type not in ["perdita_peso", "aumento_massa"]:
            raise ValueError("goal_type deve essere 'perdita_peso' o 'aumento_massa'")
        
        # Calcoli base
        kg_per_month = kg_change / time_months
        
        # Costante: 1 kg = 7700 kcal
        KCAL_PER_KG = 7700
        
        # Calcolo deficit/surplus giornaliero
        daily_calorie_adjustment = (kg_per_month * KCAL_PER_KG) / 30
        
        warnings = []
        
        if goal_type == "perdita_peso":
            # Per perdita peso, il valore deve essere negativo (deficit)
            daily_calorie_adjustment = -daily_calorie_adjustment
            
            # Verifica deficit eccessivo
            MAX_SAFE_DEFICIT = 500
            if abs(daily_calorie_adjustment) > MAX_SAFE_DEFICIT:
                warnings.append(f"Il deficit richiesto ({abs(daily_calorie_adjustment):.0f} kcal/giorno) è eccessivo. "
                               f"Raccomando un deficit massimo di {MAX_SAFE_DEFICIT} kcal/giorno per la salute.")
                daily_calorie_adjustment = -MAX_SAFE_DEFICIT
            
            # Verifica deficit vs BMR se fornito
            if bmr is not None and abs(daily_calorie_adjustment) > (bmr * 0.3):
                warnings.append(f"Il deficit potrebbe portare a un intake troppo basso rispetto al metabolismo basale "
                               f"({bmr:.0f} kcal). Considera di allungare i tempi.")
        
        else:  # aumento_massa
            # Per aumento massa, il valore deve essere positivo (surplus)
            # Surplus ottimale per minimizzare aumento grasso
            OPTIMAL_SURPLUS_MIN = 300
            OPTIMAL_SURPLUS_MAX = 500
            
            if kg_per_month > 1:
                warnings.append(f"L'aumento richiesto ({kg_per_month:.1f} kg/mese) è superiore a 1 kg/mese. "
                               "Questo potrebbe comportare un aumento del grasso corporeo oltre alla massa muscolare.")
            
            # Limita il surplus all'intervallo ottimale se eccessivo
            if daily_calorie_adjustment > OPTIMAL_SURPLUS_MAX:
                warnings.append(f"Il surplus richiesto ({daily_calorie_adjustment:.0f} kcal/giorno) è molto alto. "
                               f"Raccomando un surplus tra {OPTIMAL_SURPLUS_MIN}-{OPTIMAL_SURPLUS_MAX} kcal/giorno "
                               "per minimizzare l'aumento di grasso.")
                daily_calorie_adjustment = OPTIMAL_SURPLUS_MAX
        
        return {
            "daily_calorie_adjustment": round(daily_calorie_adjustment),
            "warnings": warnings,
            "goal_type": goal_type,
            "kg_per_month": round(kg_per_month, 2)
        }

    def analyze_bmi_and_goals(self, peso, altezza, sesso, età, obiettivo):
        """Analizza BMI, peso forma e coerenza degli obiettivi del cliente.
        
        Args:
            peso: Peso attuale in kg
            altezza: Altezza in cm
            sesso: 'maschio' o 'femmina'
            età: Età in anni
            obiettivo: 'Perdita di peso', 'Mantenimento', 'Aumento di massa'
        
        Returns:
            dict: Contiene:
                - bmi_attuale: valore BMI
                - categoria_bmi: classificazione BMI
                - peso_ideale_min: peso minimo forma
                - peso_ideale_max: peso massimo forma
                - peso_ideale_medio: peso forma medio
                - obiettivo_coerente: bool se l'obiettivo è appropriato
                - raccomandazione: testo con raccomandazione se necessario
                - warnings: lista di avvertimenti
        
        Raises:
            ValueError: se i parametri non sono validi
        """
        # Validazione parametri
        try:
            peso = float(peso)
            altezza = float(altezza)
            età = int(età)
        except (ValueError, TypeError):
            raise ValueError("Peso, altezza ed età devono essere numerici")
        
        if peso <= 0 or peso > 300:
            raise ValueError("Il peso deve essere tra 1 e 300 kg")
        
        if altezza <= 0 or altezza > 250:
            raise ValueError("L'altezza deve essere tra 1 e 250 cm")
        
        if età < 18 or età > 100:
            raise ValueError("L'età deve essere tra 18 e 100 anni")
        
        sesso = sesso.lower()
        if sesso not in ["maschio", "femmina"]:
            raise ValueError("Sesso deve essere 'maschio' o 'femmina'")
        
        obiettivi_validi = ["Perdita di peso", "Mantenimento", "Aumento di massa"]
        if obiettivo not in obiettivi_validi:
            raise ValueError(f"Obiettivo deve essere uno di: {', '.join(obiettivi_validi)}")
        
        # Calcolo BMI
        altezza_m = altezza / 100
        bmi = peso / (altezza_m ** 2)
        
        # Classificazione BMI
        if bmi < 18.5:
            categoria_bmi = "Sottopeso"
        elif bmi < 25:
            categoria_bmi = "Normopeso"
        elif bmi < 30:
            categoria_bmi = "Sovrappeso"
        else:
            categoria_bmi = "Obesità"
        
        # Calcolo peso forma (BMI normale: 18.5-24.9)
        peso_ideale_min = 18.5 * (altezza_m ** 2)
        peso_ideale_max = 24.9 * (altezza_m ** 2)
        peso_ideale_medio = 22.0 * (altezza_m ** 2)
        
        # Valutazione coerenza obiettivo
        obiettivo_coerente = True
        raccomandazione = ""
        warnings = []
        
        if categoria_bmi == "Sottopeso":
            if obiettivo == "Perdita di peso":
                obiettivo_coerente = False
                raccomandazione = (
                    f"⚠️ ATTENZIONE: Il tuo BMI è {bmi:.1f} (sottopeso). "
                    f"Perdere ulteriore peso potrebbe essere dannoso per la salute. "
                    f"Ti consiglio di puntare all'aumento di massa muscolare per raggiungere "
                    f"un peso più salutare (ideale: {peso_ideale_min:.1f}-{peso_ideale_max:.1f} kg). "
                    f"Vuoi comunque procedere con l'obiettivo di perdita di peso?"
                )
                warnings.append("BMI sotto la norma - perdita peso sconsigliata")
        
        elif categoria_bmi == "Sovrappeso" or categoria_bmi == "Obesità":
            if obiettivo == "Aumento di massa":
                obiettivo_coerente = False
                if categoria_bmi == "Sovrappeso":
                    raccomandazione = (
                        f"⚠️ ATTENZIONE: Il tuo BMI è {bmi:.1f} (sovrappeso). "
                        f"Ti consiglio di concentrarti prima sulla perdita di peso per raggiungere "
                        f"un peso più salutare (ideale: {peso_ideale_min:.1f}-{peso_ideale_max:.1f} kg), "
                        f"poi eventualmente lavorare sull'aumento di massa muscolare. "
                        f"Vuoi comunque procedere con l'obiettivo di aumento massa?"
                    )
                else:  # Obesità
                    raccomandazione = (
                        f"⚠️ ATTENZIONE: Il tuo BMI è {bmi:.1f} (obesità). "
                        f"È fortemente raccomandato concentrarsi sulla perdita di peso per motivi di salute. "
                        f"Il peso ideale sarebbe {peso_ideale_min:.1f}-{peso_ideale_max:.1f} kg. "
                        f"Procedere con aumento massa potrebbe peggiorare la situazione. "
                        f"Sei sicuro di voler mantenere questo obiettivo?"
                    )
                warnings.append("BMI elevato - aumento massa sconsigliato")
        
        elif categoria_bmi == "Normopeso":
            # Per normopeso, tutti gli obiettivi sono generalmente appropriati
            if obiettivo == "Perdita di peso" and peso <= peso_ideale_min + 2:
                # Se già nel range basso del normopeso
                warnings.append("Sei già nel range di peso ideale - valuta se la perdita è necessaria")
            elif obiettivo == "Aumento di massa" and peso >= peso_ideale_max - 2:
                # Se già nel range alto del normopeso
                warnings.append("Sei già nel range alto del peso ideale - monitora che l'aumento sia muscolare")
        
        return {
            "bmi_attuale": round(bmi, 1),
            "categoria_bmi": categoria_bmi,
            "peso_ideale_min": round(peso_ideale_min, 1),
            "peso_ideale_max": round(peso_ideale_max, 1),
            "peso_ideale_medio": round(peso_ideale_medio, 1),
            "obiettivo_coerente": obiettivo_coerente,
            "raccomandazione": raccomandazione,
            "warnings": warnings
        }

    def check_vitamins(self, foods_with_grams, sesso, età):
        """Controlla l'apporto vitaminico totale della dieta e lo confronta con i LARN.
        
        Args:
            foods_with_grams: Dizionario con alimenti e relative grammature {alimento: grammi}
            sesso: 'maschio' o 'femmina'
            età: Età in anni
        
        Returns:
            dict: Contiene:
                - total_vitamins: totali vitaminici calcolati
                - larn_requirements: fabbisogni LARN per l'utente
                - vitamin_status: stato per ogni vitamina (sufficiente/insufficiente/eccessivo)
                - warnings: lista di avvertimenti
                - recommendations: raccomandazioni specifiche
        """
        try:
            # Carica i dati degli alimenti
            foods_data = self.alimenti
            
            # Carica i LARN delle vitamine
            larn_vitamine_path = os.path.join(self.data_dir, "larn_vitamine.json")
            with open(larn_vitamine_path, 'r', encoding='utf-8') as f:
                larn_data = json.load(f)
            
            # Determina la categoria LARN appropriata
            larn_category = self._get_larn_vitamin_category(sesso, età)
            
            # Naviga nella struttura JSON per trovare i requisiti
            category_parts = larn_category.split('/')
            larn_requirements = larn_data["vitamine"]
            for part in category_parts:
                if part in larn_requirements:
                    larn_requirements = larn_requirements[part]
                else:
                    raise ValueError(f"Categoria LARN non trovata: {larn_category}")
            
            if not isinstance(larn_requirements, dict) or "vitamina_C_mg" not in larn_requirements:
                raise ValueError(f"Dati LARN non validi per categoria: {larn_category}")
            
            # Inizializza i totali vitaminici
            total_vitamins = {
                "vitamina_C_mg": 0.0, "tiamina_mg": 0.0, "riboflavina_mg": 0.0, "niacina_mg": 0.0,
                "acido_pantotenico_mg": 0.0, "vitamina_B6_mg": 0.0, "biotina_ug": 0.0, "folati_ug": 0.0,
                "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.0, "vitamina_K_ug": 0.0
            }
            
            # Calcola i totali per ogni alimento
            foods_not_found = []
            for food_name, grams in foods_with_grams.items():
                if food_name in foods_data:
                    food_data = foods_data[food_name]
                    # Calcola l'apporto vitaminico per la quantità specificata
                    for vitamin in total_vitamins.keys():
                        if vitamin in food_data:
                            total_vitamins[vitamin] += (food_data[vitamin] * grams) / 100.0
                else:
                    foods_not_found.append(food_name)
            
            # Arrotonda i valori
            for vitamin in total_vitamins:
                total_vitamins[vitamin] = round(total_vitamins[vitamin], 2)
            
            # Confronta con i LARN e determina lo stato
            vitamin_status = {}
            warnings = []
            recommendations = []
            
            for vitamin, total_amount in total_vitamins.items():
                if vitamin in larn_requirements:
                    required_amount = larn_requirements[vitamin]
                    percentage = (total_amount / required_amount) * 100 if required_amount > 0 else 0
                    
                    if percentage < 70:
                        status = "insufficiente"
                        warnings.append(f"{vitamin}: {total_amount:.2f} (solo {percentage:.1f}% del fabbisogno)")
                        recommendations.append(self._get_vitamin_recommendation(vitamin))
                    elif percentage > 300:  # Soglia per eccesso (3x il fabbisogno)
                        status = "eccessivo"
                        warnings.append(f"{vitamin}: {total_amount:.2f} (eccesso: {percentage:.1f}% del fabbisogno)")
                    else:
                        status = "sufficiente"
                    
                    vitamin_status[vitamin] = {
                        "amount": total_amount,
                        "required": required_amount,
                        "percentage": round(percentage, 1),
                        "status": status
                    }
            
            # Aggiungi avvertimenti per alimenti non trovati
            if foods_not_found:
                warnings.append(f"Alimenti non trovati nel database: {', '.join(foods_not_found)}")
            
            # Rimuovi duplicati dalle raccomandazioni
            recommendations = list(set(recommendations))
            
            return {
                "total_vitamins": total_vitamins,
                "larn_requirements": larn_requirements,
                "vitamin_status": vitamin_status,
                "warnings": warnings,
                "recommendations": recommendations,
                "foods_not_found": foods_not_found
            }
            
        except Exception as e:
            raise ValueError(f"Errore nel controllo vitaminico: {str(e)}")
    
    def _get_larn_vitamin_category(self, sesso, età):
        """Determina la categoria LARN appropriata per le vitamine."""
        sesso = sesso.lower()
        
        if età < 1:
            return "lattanti/6_12_mesi"
        elif età <= 3:
            return "bambini_adolescenti/1_3_anni"
        elif età <= 6:
            return "bambini_adolescenti/4_6_anni"
        elif età <= 10:
            return "bambini_adolescenti/7_10_anni"
        elif età <= 14:
            if sesso in ["maschio", "m"]:
                return "bambini_adolescenti/maschi_11_14_anni"
            else:
                return "bambini_adolescenti/femmine_11_14_anni"
        elif età <= 17:
            if sesso in ["maschio", "m"]:
                return "bambini_adolescenti/maschi_15_17_anni"
            else:
                return "bambini_adolescenti/femmine_15_17_anni"
        elif età <= 29:
            if sesso in ["maschio", "m"]:
                return "adulti/maschi_18_29"
            else:
                return "adulti/femmine_18_29"
        elif età <= 59:
            if sesso in ["maschio", "m"]:
                return "adulti/maschi_30_59"
            else:
                return "adulti/femmine_30_59"
        elif età <= 74:
            if sesso in ["maschio", "m"]:
                return "adulti/maschi_60_74"
            else:
                return "adulti/femmine_60_74"
        else:
            if sesso in ["maschio", "m"]:
                return "adulti/maschi_75_plus"
            else:
                return "adulti/femmine_75_plus"
    
    def _get_vitamin_recommendation(self, vitamin):
        """Restituisce raccomandazioni specifiche per ogni vitamina."""
        recommendations = {
            "vitamina_C_mg": "Aumenta il consumo di agrumi, kiwi, fragole, peperoni, broccoli",
            "tiamina_mg": "Aumenta il consumo di cereali integrali, legumi, carne di maiale",
            "riboflavina_mg": "Aumenta il consumo di latte, uova, verdure a foglia verde",
            "niacina_mg": "Aumenta il consumo di carne, pesce, cereali integrali, arachidi",
            "acido_pantotenico_mg": "Aumenta il consumo di carne, uova, legumi, cereali integrali",
            "vitamina_B6_mg": "Aumenta il consumo di carne, pesce, patate, banane",
            "biotina_ug": "Aumenta il consumo di uova, noci, semi, fegato",
            "folati_ug": "Aumenta il consumo di verdure a foglia verde, legumi, agrumi",
            "vitamina_B12_ug": "Aumenta il consumo di carne, pesce, uova, latticini",
            "vitamina_A_ug": "Aumenta il consumo di carote, spinaci, fegato, uova",
            "vitamina_D_ug": "Aumenta l'esposizione al sole e il consumo di pesce grasso, uova",
            "vitamina_E_mg": "Aumenta il consumo di oli vegetali, noci, semi, verdure a foglia verde",
            "vitamina_K_ug": "Aumenta il consumo di verdure a foglia verde, broccoli, cavoli"
        }
        return recommendations.get(vitamin, "Consulta un nutrizionista per consigli specifici")

    def get_food_substitutes(self, food_name, grams, num_substitutes=5):
        """Ottiene gli alimenti sostitutivi per un dato alimento e quantità.
        
        Args:
            food_name: Nome dell'alimento per cui cercare sostituti
            grams: Grammi dell'alimento di riferimento
            num_substitutes: Numero massimo di sostituti da restituire (default 5)
        
        Returns:
            dict: Contiene:
                - substitutes: lista di sostituti con grammature equivalenti
                - reference_food: dati dell'alimento di riferimento
                - available: bool se il sistema di sostituti è disponibile
        
        Raises:
            ValueError: se l'alimento non è trovato o i grammi non sono validi
        """
        if self.substitutes is None:
            return {
                "available": False,
                "error": "Database dei sostituti non disponibile",
                "substitutes": [],
                "reference_food": None
            }
        
        # Validazione grammi
        try:
            grams = float(grams)
            if grams <= 0:
                raise ValueError("I grammi devono essere positivi")
        except (ValueError, TypeError):
            raise ValueError("I grammi devono essere un numero positivo")
        
        # Normalizza il nome dell'alimento usando gli alias
        normalized_name = self.alias.get(food_name.lower().replace("_", " "))
        if not normalized_name:
            normalized_name = food_name
        
        # Verifica che l'alimento esista nel database principale
        if normalized_name not in self.alimenti:
            raise ValueError(f"Alimento '{food_name}' non trovato nel database")
        
        # Verifica che l'alimento abbia sostituti
        if normalized_name not in self.substitutes.get("substitutes", {}):
            return {
                "available": True,
                "substitutes": [],
                "reference_food": {
                    "name": normalized_name,
                    "grams": grams,
                    "data": self.alimenti[normalized_name]
                },
                "message": f"Nessun sostituto disponibile per {normalized_name}"
            }
        
        # Ottieni i sostituti
        food_substitutes = self.substitutes["substitutes"][normalized_name]
        reference_food_data = self.alimenti[normalized_name]
        
        # Calcola i valori nutrizionali dell'alimento di riferimento per la quantità specificata
        reference_nutrition = {
            "energia_kcal": round((reference_food_data.get("energia_kcal", 0) * grams) / 100, 1),
            "proteine_g": round((reference_food_data.get("proteine_g", 0) * grams) / 100, 1),
            "carboidrati_g": round((reference_food_data.get("carboidrati_g", 0) * grams) / 100, 1),
            "grassi_g": round((reference_food_data.get("grassi_g", 0) * grams) / 100, 1)
        }
        
        # Prepara la lista dei sostituti con i loro dati nutrizionali
        substitutes_list = []
        count = 0
        
        for substitute_name, substitute_info in food_substitutes.items():
            if count >= num_substitutes:
                break
                
            if substitute_name in self.alimenti:
                substitute_data = self.alimenti[substitute_name]
                
                # Calcola i grammi equivalenti per la quantità specificata
                # I grammi nel database sono per 100g di alimento di riferimento
                # Quindi per X grammi: (X / 100) * grammi_sostituto_per_100g
                equivalent_grams_for_quantity = round((grams / 100) * substitute_info["grams"], 1)
                
                # Calcola i valori nutrizionali del sostituto per la quantità equivalente
                substitute_nutrition = {
                    "energia_kcal": round((substitute_data.get("energia_kcal", 0) * equivalent_grams_for_quantity) / 100, 1),
                    "proteine_g": round((substitute_data.get("proteine_g", 0) * equivalent_grams_for_quantity) / 100, 1),
                    "carboidrati_g": round((substitute_data.get("carboidrati_g", 0) * equivalent_grams_for_quantity) / 100, 1),
                    "grassi_g": round((substitute_data.get("grassi_g", 0) * equivalent_grams_for_quantity) / 100, 1)
                }
                
                substitutes_list.append({
                    "name": substitute_name,
                    "equivalent_grams": equivalent_grams_for_quantity,
                    "similarity_score": substitute_info["similarity_score"],
                    "nutritional_data_per_100g": {
                        "energia_kcal": substitute_data.get("energia_kcal", 0),
                        "proteine_g": substitute_data.get("proteine_g", 0),
                        "carboidrati_g": substitute_data.get("carboidrati_g", 0),
                        "grassi_g": substitute_data.get("grassi_g", 0)
                    },
                    "equivalent_nutrition": substitute_nutrition
                })
                count += 1
        
        return {
            "available": True,
            "substitutes": substitutes_list,
            "reference_food": {
                "name": normalized_name,
                "grams": grams,
                "data": reference_food_data,
                "nutrition": reference_nutrition
            },
            "metadata": {
                "reference_amount": f"{grams}g",
                "calculation_method": "Equivalenza calorica con priorità per similarità macronutrienti"
            }
        }

    def check_foods_in_db(self, food_list):
        """Verifica se una lista di alimenti è presente nel database.
        
        Args:
            food_list: Lista di nomi di alimenti da verificare
            
        Returns:
            tuple: (all_found: bool, foods_not_found: list)
                - all_found: True se tutti gli alimenti sono trovati, False altrimenti
                - foods_not_found: Lista degli alimenti non trovati nel database
        """
        foods_not_found = []
        
        for food in food_list:
            # Applica la logica di normalizzazione utilizzata nella classe
            normalized_food = food.lower().replace("_", " ")
            
            # Controlla se l'alimento è presente negli alias
            if normalized_food not in self.alias:
                foods_not_found.append(food)
        
        all_found = len(foods_not_found) == 0
        
        return all_found, foods_not_found
