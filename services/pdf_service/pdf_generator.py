"""
Generatore di PDF per il piano nutrizionale.

Questo modulo contiene la classe PDFGenerator che crea documenti PDF
completi con tutti i dati del piano nutrizionale dell'utente.
"""

import os
import json
import io
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
import reportlab.lib.colors as colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, CondPageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class SmartDocTemplate(SimpleDocTemplate):
    """
    Estensione di SimpleDocTemplate che rimuove automaticamente le pagine vuote.
    """
    
    def build(self, flowables, **kwargs):
        """
        Sovrascrivo il metodo build per rimuovere le pagine vuote.
        """
        # Filtra gli elementi per rimuovere PageBreak consecutivi e quelli alla fine
        filtered_flowables = self._remove_empty_pages(flowables)
        
        # Chiama il metodo build originale con la story filtrata
        super().build(filtered_flowables, **kwargs)
    
    def _remove_empty_pages(self, flowables):
        """
        Rimuove i PageBreak che creerebbero pagine vuote.
        """
        if not flowables:
            return flowables
        
        filtered = []
        last_was_pagebreak = False
        
        for i, item in enumerate(flowables):
            is_pagebreak = isinstance(item, PageBreak)
            
            # Salta PageBreak consecutivi
            if is_pagebreak and last_was_pagebreak:
                continue
            
            # Salta PageBreak all'inizio
            if is_pagebreak and len(filtered) == 0:
                continue
            
            # Salta PageBreak alla fine
            if is_pagebreak and i == len(flowables) - 1:
                continue
            
            # Controlla se c'è contenuto significativo dopo un PageBreak
            if is_pagebreak:
                has_content_after = self._has_meaningful_content_after(flowables, i)
                if not has_content_after:
                    continue
            
            filtered.append(item)
            last_was_pagebreak = is_pagebreak
        
        return filtered
    
    def _has_meaningful_content_after(self, flowables, pagebreak_index):
        """
        Verifica se c'è contenuto significativo dopo un PageBreak.
        """
        for item in flowables[pagebreak_index + 1:]:
            # Ignora altri PageBreak
            if isinstance(item, PageBreak):
                continue
            
            # Ignora Spacer molto piccoli (meno di 20 punti)
            if isinstance(item, Spacer) and item.height < 20:
                continue
            
            # Se troviamo qualsiasi altro elemento, c'è contenuto
            return True
        
        return False


class PDFGenerator:
    """Genera documenti PDF per il piano nutrizionale dell'utente"""
    
    def __init__(self):
        """Inizializza il generatore PDF con stili e configurazioni"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura gli stili personalizzati per il PDF"""
        # Titolo principale
        self.styles.add(ParagraphStyle(
            name='CustomMainTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=HexColor('#1f77b4'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        # Sottotitoli sezioni
        self.styles.add(ParagraphStyle(
            name='CustomSectionTitle',
            parent=self.styles['Heading1'],
            fontSize=14,  # Font più piccolo
            textColor=HexColor('#2c3e50'),
            spaceBefore=10,  # Spazio ridotto
            spaceAfter=6,  # Spazio ridotto
            fontName='Helvetica-Bold'
        ))
        
        # Sottotitoli minori
        self.styles.add(ParagraphStyle(
            name='CustomSubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#34495e'),
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Testo normale con margini
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=HexColor('#2c3e50'),
            spaceAfter=6,
            leftIndent=10
        ))
        
        # Testo centrato
        self.styles.add(ParagraphStyle(
            name='CustomCenteredText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        
        # Info di header
        self.styles.add(ParagraphStyle(
            name='CustomHeaderInfo',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=HexColor('#7f8c8d'),
            alignment=TA_RIGHT,
            spaceAfter=15
        ))
    
    def generate_nutritional_plan_pdf(self, user_id: str, user_info: Dict[str, Any]) -> bytes:
        """
        Genera un PDF completo del piano nutrizionale.
        
        Args:
            user_id: ID dell'utente
            user_info: Informazioni base dell'utente
            
        Returns:
            bytes: Contenuto del PDF generato
            
        Raises:
            ValueError: Se i dati nutrizionali non sono disponibili
            FileNotFoundError: Se il file utente non esiste
        """
        # Carica i dati nutrizionali
        extracted_data = self._load_user_nutritional_data(user_id)
        if not extracted_data:
            raise ValueError("Nessun dato nutrizionale estratto disponibile per questo utente")
        
        # Crea il buffer per il PDF
        buffer = io.BytesIO()
        
        # Crea il documento PDF con rimozione automatica delle pagine vuote
        doc = SmartDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # Costruisci il contenuto del PDF
        story = []
        
        # Header del documento
        self._add_document_header(story, user_info, extracted_data)
        
        # Sezioni principali - prime tre tabelle nella prima pagina
        self._add_caloric_needs_section(story, extracted_data)
        self._add_macros_section(story, extracted_data)
        self._add_daily_plan_section(story, extracted_data)
        
        # Forza una nuova pagina per la dieta settimanale se rimane più spazio di quello 
        # necessario per un titolo e poco contenuto. Con 700 punti (circa 25cm) forziamo 
        # praticamente sempre una nuova pagina, assicurando che il Giorno 1 inizi sempre in pagina 2
        story.append(CondPageBreak(700))  # 700 punti = forza nuova pagina nella maggior parte dei casi
        self._add_weekly_diet_section(story, extracted_data)
        
        # Footer informativo
        self._add_document_footer(story)
        
        # Genera il PDF con rimozione automatica delle pagine vuote
        doc.build(story)
        
        # Restituisci i bytes del PDF
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _load_user_nutritional_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati nutrizionali dell'utente dal file JSON.
        Gestisce entrambi i formati di file: user_data/{user_id}.json e user_data/user_{user_id}.json
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            dict: Dati nutrizionali estratti o None se non trovati
        """
        # Percorsi possibili per il file utente
        possible_paths = [
            f"user_data/{user_id}.json",
            f"user_data/user_{user_id}.json"
        ]
        
        user_data = None
        
        # Prova i percorsi possibili
        for user_file_path in possible_paths:
            if os.path.exists(user_file_path):
                try:
                    with open(user_file_path, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    print(f"[PDF_SERVICE] File utente caricato da: {user_file_path}")
                    break
                except (json.JSONDecodeError, Exception) as e:
                    print(f"[PDF_ERROR] Errore lettura {user_file_path}: {str(e)}")
                    continue
        
        if not user_data:
            print(f"[PDF_ERROR] File utente non trovato per user_id: {user_id}")
            print(f"[PDF_ERROR] Percorsi cercati: {possible_paths}")
            return None
        
        # Estrai i dati nutrizionali
        nutritional_data = user_data.get("nutritional_info_extracted", {})
        
        if not nutritional_data:
            print(f"[PDF_ERROR] Nessun dato nutrizionale estratto trovato per user_id: {user_id}")
            return None
        
        print(f"[PDF_SERVICE] Dati nutrizionali caricati con successo per user_id: {user_id}")
        return nutritional_data
    
    def _add_document_header(self, story: list, user_info: Dict[str, Any], extracted_data: Dict[str, Any]):
        """
        Aggiunge l'header del documento con titolo e informazioni utente.
        
        Args:
            story: Lista degli elementi del PDF
            user_info: Informazioni dell'utente
            extracted_data: Dati nutrizionali estratti
        """
        # Titolo principale
        title = Paragraph("🥗 NutriCoach - Piano Nutrizionale Personalizzato", self.styles['CustomMainTitle'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Informazioni utente e data di generazione (non ultimo aggiornamento dati)
        username = user_info.get('username', 'Utente')
        current_date = datetime.now().strftime("%d/%m/%Y alle %H:%M")
        
        header_info = f"Piano per: <b>{username}</b> | Generato il: {current_date}"
        story.append(Paragraph(header_info, self.styles['CustomHeaderInfo']))
        
        # Informazioni personali se disponibili
        if user_info.get('età'):
            personal_info = [
                ['Età:', f"{user_info.get('età', 'N/A')} anni"],
                ['Sesso:', user_info.get('sesso', 'N/A')],
                ['Peso:', f"{user_info.get('peso', 'N/A')} kg"],
                ['Altezza:', f"{user_info.get('altezza', 'N/A')} cm"],
                ['Attività:', user_info.get('attività', 'N/A')],
                ['Obiettivo:', user_info.get('obiettivo', 'N/A')]
            ]
            
            personal_table = Table(personal_info, colWidths=[1.5*inch, 2*inch])
            personal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            story.append(personal_table)
            story.append(Spacer(1, 20))
    
    def _add_caloric_needs_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione del fabbisogno energetico.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "caloric_needs" not in extracted_data:
            print("[PDF_SERVICE] Sezione caloric_needs saltata - dati non disponibili")
            return
        
        caloric_data = extracted_data["caloric_needs"]
        if not caloric_data:
            print("[PDF_SERVICE] Sezione caloric_needs saltata - dati vuoti")
            return
        
        # Titolo sezione più compatto
        story.append(Paragraph("🔥 Fabbisogno Energetico Giornaliero", self.styles['CustomSectionTitle']))
        
        # Tabella con i valori calorici - più compatta
        caloric_table_data = [
            ['Parametro', 'Valore', 'Descrizione'],
            ['Metabolismo Basale (BMR)', f"{caloric_data.get('bmr', 0)} kcal", 'Energia per le funzioni vitali'],
            ['Fabbisogno Base', f"{caloric_data.get('fabbisogno_base', 0)} kcal", 'Con attività quotidiana'],
            ['Dispendio Sportivo', f"{caloric_data.get('dispendio_sportivo', 0)} kcal", 'Calorie dall\'attività sportiva'],
            ['Fabbisogno Totale', f"{caloric_data.get('fabbisogno_totale', 0)} kcal", 'Calorie totali giornaliere']
        ]
        
        caloric_table = Table(caloric_table_data, colWidths=[2.0*inch, 1.3*inch, 1.5*inch, 1.2*inch])
        caloric_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498db')),  # Blu
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Font più piccolo
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Font più piccolo
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),  # Padding ridotto
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),  # Padding ridotto
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]))
        
        story.append(caloric_table)
        
        # Informazioni aggiuntive più compatte
        additional_info = []
        
        aggiustamento = caloric_data.get('aggiustamento_obiettivo', 0)
        if aggiustamento != 0:
            simbolo = "+" if aggiustamento > 0 else ""
            additional_info.append(f"<b>Aggiustamento Obiettivo:</b> {simbolo}{aggiustamento} kcal")
        
        if additional_info:
            story.append(Spacer(1, 5))  # Spazio ridotto
            for info in additional_info:
                story.append(Paragraph(info, self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 15))  # Spazio ridotto
    
    def _add_macros_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione dei macronutrienti.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "macros_total" not in extracted_data:
            print("[PDF_SERVICE] Sezione macros_total saltata - dati non disponibili")
            return
        
        macros_data = extracted_data["macros_total"]
        if not macros_data:
            print("[PDF_SERVICE] Sezione macros_total saltata - dati vuoti")
            return
        
        # Titolo sezione più compatto
        story.append(Paragraph("🥗 Distribuzione Calorica Giornaliera", self.styles['CustomSectionTitle']))
        
        # Tabella macronutrienti - più compatta
        macros_table_data = [
            ['Macronutriente', 'Grammi', 'Calorie', 'Percentuale'],
            ['Proteine', f"{macros_data.get('proteine_g', 0)}g", f"{macros_data.get('proteine_kcal', 0)} kcal", f"{macros_data.get('proteine_percentuale', 0)}%"],
            ['Carboidrati', f"{macros_data.get('carboidrati_g', 0)}g", f"{macros_data.get('carboidrati_kcal', 0)} kcal", f"{macros_data.get('carboidrati_percentuale', 0)}%"],
            ['Grassi', f"{macros_data.get('grassi_g', 0)}g", f"{macros_data.get('grassi_kcal', 0)} kcal", f"{macros_data.get('grassi_percentuale', 0)}%"]
        ]
        
        macros_table = Table(macros_table_data, colWidths=[2.0*inch, 1.3*inch, 1.5*inch, 1.2*inch])
        macros_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e74c3c')),  # Rosso
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Font più piccolo
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Font più piccolo
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),  # Padding ridotto
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),  # Padding ridotto
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]))
        
        story.append(macros_table)
        
        # Totali aggiuntivi più compatti
        story.append(Spacer(1, 5))  # Spazio ridotto
        totals_info = []
        
        fibre = macros_data.get('fibre_g', 0)
        if fibre > 0:
            totals_info.append(f"<b>Fibre giornaliere:</b> {fibre}g")
        
        kcal_totali = macros_data.get('kcal_totali', 0)
        totals_info.append(f"<b>Calorie Totali:</b> {kcal_totali} kcal")
        
        for info in totals_info:
            story.append(Paragraph(info, self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 15))  # Spazio ridotto
    
    def _add_daily_plan_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione del piano pasti giornaliero.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "daily_macros" not in extracted_data:
            print("[PDF_SERVICE] Sezione daily_macros saltata - dati non disponibili")
            return
        
        daily_data = extracted_data["daily_macros"]
        if not daily_data:
            print("[PDF_SERVICE] Sezione daily_macros saltata - dati vuoti")
            return
        
        # Titolo sezione più compatto
        story.append(Paragraph("🍽️ Piano Pasti Giornaliero", self.styles['CustomSectionTitle']))
        
        num_pasti = daily_data.get('numero_pasti', 0)
        story.append(Paragraph(f"<b>Piano giornaliero:</b> {num_pasti} pasti", self.styles['CustomBodyText']))
        story.append(Spacer(1, 5))  # Spazio ridotto
        
        if "distribuzione_pasti" not in daily_data:
            return
        
        # Tabella distribuzione pasti - più compatta
        distribuzione_pasti = daily_data["distribuzione_pasti"]
        meal_table_data = [['Pasto', 'Calorie', '% del Totale', 'Proteine', 'Carboidrati', 'Grassi']]
        
        for pasto_nome, pasto_data in distribuzione_pasti.items():
            # Controllo di sicurezza per pasto_data
            if not pasto_data:
                print(f"[PDF_SERVICE] Saltato pasto '{pasto_nome}' - dati vuoti")
                continue
                
            kcal = pasto_data.get('kcal', 0)
            percentuale = pasto_data.get('percentuale_kcal', 0)
            proteine = pasto_data.get('proteine_g', 0)
            carboidrati = pasto_data.get('carboidrati_g', 0)
            grassi = pasto_data.get('grassi_g', 0)
            
            meal_table_data.append([
                pasto_nome.title(),
                f"{kcal} kcal",
                f"{percentuale}%",
                f"{proteine}g",
                f"{carboidrati}g",
                f"{grassi}g"
            ])
        
        meal_table = Table(meal_table_data, colWidths=[1.5*inch, 1.0*inch, 0.8*inch, 0.8*inch, 1.0*inch, 0.9*inch])
        meal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f39c12')),  # Arancione
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Font più piccolo
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Font più piccolo
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),  # Padding ridotto
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),  # Padding ridotto
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
        ]))
        
        story.append(meal_table)
        story.append(Spacer(1, 15))  # Spazio ridotto
    
    def _add_registered_meals_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione dei pasti registrati.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "registered_meals" not in extracted_data or not extracted_data["registered_meals"]:
            print("[PDF_SERVICE] Sezione registered_meals saltata - dati non disponibili")
            return
        
        meals_data = extracted_data["registered_meals"]
        
        # Titolo sezione
        story.append(Paragraph("👨‍🍳 Ricette e Pasti Creati", self.styles['CustomSectionTitle']))
        
        # Ordina i pasti in ordine cronologico corretto
        sorted_meals = self._sort_meals_by_time(meals_data)
        
        for i, meal in enumerate(sorted_meals):
            nome_pasto = meal.get('nome_pasto', 'Pasto').title()
            
            # Sottotitolo del pasto
            story.append(Paragraph(f"🍽️ {nome_pasto}", self.styles['CustomSubTitle']))
            
            # Ingredienti
            if "alimenti" in meal and meal["alimenti"]:
                story.append(Paragraph("<b>Ingredienti:</b>", self.styles['CustomBodyText']))
                
                ingredients_data = [['Alimento', 'Quantità', 'Misura Casalinga']]
                
                for alimento in meal["alimenti"]:
                    # Controllo di sicurezza per alimento
                    if not alimento:
                        print("[PDF_SERVICE] Saltato alimento vuoto")
                        continue
                        
                    nome = alimento.get('nome_alimento', 'N/A')
                    quantita = alimento.get('quantita_g', 'N/A')
                    misura = alimento.get('misura_casalinga', 'N/A')
                    
                    ingredients_data.append([nome, f"{quantita}g", misura])
                
                ingredients_table = Table(ingredients_data, colWidths=[2.7*inch, 1.2*inch, 2.7*inch])
                ingredients_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#8e44ad')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                    ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
                ]))
                
                story.append(ingredients_table)
                story.append(Spacer(1, 10))
            
            # Totali nutrizionali
            if "totali_pasto" in meal:
                totali = meal["totali_pasto"]
                
                # Controllo di sicurezza per totali
                if not totali:
                    print(f"[PDF_SERVICE] Saltati totali per pasto '{nome_pasto}' - dati vuoti")
                else:
                    totals_data = [
                        ['Calorie Totali', 'Proteine Totali', 'Carboidrati Totali', 'Grassi Totali'],
                        [
                            f"{totali.get('kcal_totali', 0)} kcal",
                            f"{totali.get('proteine_totali', 0)}g",
                            f"{totali.get('carboidrati_totali', 0)}g",
                            f"{totali.get('grassi_totali', 0)}g"
                        ]
                    ]
                    
                    totals_table = Table(totals_data, colWidths=[1.6*inch, 1.6*inch, 1.6*inch, 1.6*inch])
                    totals_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f39c12')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#fff3cd')),
                        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
                    ]))
                    
                    story.append(totals_table)
            
            # Separatore tra pasti (tranne l'ultimo)
            if i < len(meals_data) - 1:
                story.append(Spacer(1, 15))
        
        story.append(Spacer(1, 20))
    
    def _add_weekly_diet_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione della dieta settimanale completa (giorni 1-7).
        Ogni giorno viene posizionato su una pagina separata.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        # Verifica che ci siano dati da mostrare
        has_day1_data = "registered_meals" in extracted_data and extracted_data["registered_meals"]
        has_weekly_data = "weekly_diet" in extracted_data and extracted_data["weekly_diet"]
        
        if not has_day1_data and not has_weekly_data:
            print("[PDF_SERVICE] Sezione weekly_diet saltata - nessun dato disponibile")
            return
        # Nomi dei giorni
        day_names = {
            1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì", 
            5: "Venerdì", 6: "Sabato", 7: "Domenica"
        }
        
        # Mostra tutti i giorni 1-7
        for day_num in range(1, 8):
            # Inizia una nuova pagina per ogni giorno (tranne il primo)
            if day_num > 1:
                story.append(PageBreak())
            
            day_name = day_names.get(day_num, f"Giorno {day_num}")
            
            # Header del giorno
            story.append(Paragraph(f"📆 {day_name} (Giorno {day_num})", self.styles['CustomSectionTitle']))
            story.append(Spacer(1, 15))
            
            if day_num == 1 and has_day1_data:
                # Giorno 1: dati da registered_meals
                self._add_day1_meals_to_pdf(story, extracted_data["registered_meals"])
            elif day_num > 1 and has_weekly_data:
                # Giorni 2-7: dati da weekly_diet
                weekly_diet = extracted_data["weekly_diet"]
                day_key = f"giorno_{day_num}"
                if day_key in weekly_diet and weekly_diet[day_key]:
                    day_data = weekly_diet[day_key]
                    self._add_weekly_diet_day_to_pdf(story, day_data)
                else:
                    story.append(Paragraph("📝 Nessun piano disponibile per questo giorno", self.styles['CustomBodyText']))
            else:
                story.append(Paragraph("📝 Nessun piano disponibile per questo giorno", self.styles['CustomBodyText']))
            
            # Aggiungi spazio alla fine della pagina se non è l'ultimo giorno
            if day_num < 7:
                story.append(Spacer(1, 30))
    
    def _add_day1_meals_to_pdf(self, story: list, registered_meals: list):
        """
        Aggiunge i pasti del giorno 1 (da registered_meals) al PDF.
        
        Args:
            story: Lista degli elementi del PDF
            registered_meals: Lista dei pasti registrati del giorno 1
        """
        if not registered_meals:
            story.append(Paragraph("📝 Nessun pasto disponibile per questo giorno", self.styles['CustomBodyText']))
            return
        
        # Ordina i pasti
        sorted_meals = self._sort_meals_by_time(registered_meals)
        
        # Conta i pasti per determinare se serve layout compatto
        meals_count = len(sorted_meals)
        is_compact = meals_count > 4
        
        for meal in sorted_meals:
            nome_pasto = meal.get('nome_pasto', 'Pasto').title()
            
            # Sottotitolo del pasto
            meal_display_names = {
                'colazione': '🌅 Colazione',
                'spuntino_mattutino': '🥤 Spuntino Mattutino', 
                'pranzo': '🍽️ Pranzo',
                'spuntino_pomeridiano': '🥨 Spuntino Pomeridiano',
                'cena': '🌙 Cena',
                'spuntino_serale': '🌃 Spuntino Serale'
            }
            
            canonical_name = nome_pasto.lower().replace(' ', '_')
            display_name = meal_display_names.get(canonical_name, f'🍽️ {nome_pasto}')
            
            story.append(Paragraph(display_name, self.styles['CustomSubTitle']))
            
            # Ingredienti
            if "alimenti" in meal and meal["alimenti"]:
                ingredients_data = [['Alimento', 'Quantità', 'Misura Casalinga']]
                
                for alimento in meal["alimenti"]:
                    if not alimento:
                        continue
                    nome = alimento.get('nome_alimento', 'N/A')
                    quantita = alimento.get('quantita_g', 'N/A')
                    misura = alimento.get('misura_casalinga', 'N/A')
                    ingredients_data.append([nome, f"{quantita}g", misura])
                
                if len(ingredients_data) > 1:
                    # Usa dimensioni compatte se ci sono più di 4 pasti
                    if is_compact:
                        col_widths = [2.2*inch, 1.0*inch, 2.3*inch]  # Ridotte
                        header_font = 10  # Aumentato da 7 a 8
                        content_font = 9  # Aumentato da 6 a 7
                        padding = 3
                    else:
                        col_widths = [2.7*inch, 1.2*inch, 2.7*inch]  # Standard
                        header_font = 11  # Aumentato da 8 a 9
                        content_font = 10  # Aumentato da 7 a 8
                        padding = 5
                    
                    ingredients_table = Table(ingredients_data, colWidths=col_widths)
                    ingredients_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#27ae60')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), header_font),
                        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), content_font),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), padding),
                        ('RIGHTPADDING', (0, 0), (-1, -1), padding),
                        ('TOPPADDING', (0, 0), (-1, -1), padding),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), padding)
                    ]))
                    
                    story.append(ingredients_table)
            
            # Usa spazio ridotto se ci sono molti pasti
            space_after_meal = 8 if is_compact else 15
            story.append(Spacer(1, space_after_meal))
    
    def _add_weekly_diet_day_to_pdf(self, story: list, day_data: Dict[str, Any]):
        """
        Aggiunge i pasti di un giorno dalla weekly_diet al PDF.
        
        Args:
            story: Lista degli elementi del PDF
            day_data: Dati del giorno dalla weekly_diet
        """
        # Ordine dei pasti
        meal_order = ['colazione', 'spuntino_mattutino', 'pranzo', 'spuntino_pomeridiano', 'cena', 'spuntino_serale']
        
        # Conta i pasti totali per determinare se serve layout compatto
        total_meals = sum(1 for meal_name in meal_order if meal_name in day_data and day_data[meal_name])
        if total_meals == 0:
            total_meals = sum(1 for meal_data in day_data.values() if meal_data)
        is_compact = total_meals > 4
        
        meals_found = 0
        for meal_name in meal_order:
            if meal_name in day_data and day_data[meal_name]:
                meal_data = day_data[meal_name]
                self._add_weekly_diet_meal_to_pdf(story, meal_name, meal_data, is_compact)
                meals_found += 1
        
        # Se non ci sono pasti nell'ordine standard, mostra tutti quelli disponibili
        if meals_found == 0:
            for meal_name, meal_data in day_data.items():
                if meal_data:
                    self._add_weekly_diet_meal_to_pdf(story, meal_name, meal_data, is_compact)
    
    def _add_weekly_diet_meal_to_pdf(self, story: list, meal_name: str, meal_data: Dict[str, Any], is_compact: bool = False):
        """
        Aggiunge un singolo pasto della weekly diet al PDF.
        
        Args:
            story: Lista degli elementi del PDF
            meal_name: Nome del pasto
            meal_data: Dati del pasto
            is_compact: Se True, usa layout compatto per molti pasti
        """
        # Converti il nome del pasto in forma leggibile
        meal_display_names = {
            'colazione': '🌅 Colazione',
            'spuntino_mattutino': '🥤 Spuntino Mattutino', 
            'pranzo': '🍽️ Pranzo',
            'spuntino_pomeridiano': '🥨 Spuntino Pomeridiano',
            'cena': '🌙 Cena',
            'spuntino_serale': '🌃 Spuntino Serale'
        }
        
        display_name = meal_display_names.get(meal_name, f'🍽️ {meal_name.title()}')
        
        # Sottotitolo del pasto
        story.append(Paragraph(display_name, self.styles['CustomSubTitle']))
        
        # Alimenti del pasto
        if "alimenti" not in meal_data or not meal_data["alimenti"]:
            return
        
        alimenti = meal_data["alimenti"]
        ingredients_data = [['Alimento', 'Quantità', 'Misura Casalinga']]
        
        # Gestisce sia formato lista che formato dizionario
        if isinstance(alimenti, list):
            # Formato lista: [{"nome_alimento": "...", "quantita_g": ...}]
            for alimento in alimenti:
                if not alimento:
                    continue
                nome = alimento.get('nome_alimento', 'N/A')
                quantita = alimento.get('quantita_g', 'N/A')
                misura = alimento.get('misura_casalinga', 'N/A')
                ingredients_data.append([nome, f"{quantita}g", misura])
        
        elif isinstance(alimenti, dict):
            # Formato dizionario: {"alimento": quantita}
            for nome_alimento, quantita in alimenti.items():
                if quantita and quantita > 0:
                    ingredients_data.append([nome_alimento, f"{quantita}g", "N/A"])
        
        # Se ci sono ingredienti, crea la tabella
        if len(ingredients_data) > 1:
            # Usa dimensioni compatte se ci sono più di 4 pasti
            if is_compact:
                col_widths = [2.2*inch, 1.0*inch, 2.3*inch]  # Ridotte
                header_font = 10  # Aumentato da 7 a 8
                content_font = 9  # Aumentato da 6 a 7
                padding = 3
            else:
                col_widths = [2.7*inch, 1.2*inch, 2.7*inch]  # Standard
                header_font = 11  # Aumentato da 8 a 9
                content_font = 10  # Aumentato da 7 a 8
                padding = 5
            
            ingredients_table = Table(ingredients_data, colWidths=col_widths)
            ingredients_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_font),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), content_font),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), padding),
                ('RIGHTPADDING', (0, 0), (-1, -1), padding),
                ('TOPPADDING', (0, 0), (-1, -1), padding),
                ('BOTTOMPADDING', (0, 0), (-1, -1), padding)
            ]))
            
            story.append(ingredients_table)
        
        # Valori nutrizionali se disponibili
        if "target_nutrients" in meal_data or "actual_nutrients" in meal_data:
            nutrients = meal_data.get("actual_nutrients", meal_data.get("target_nutrients", {}))
            if nutrients:
                self._add_weekly_diet_nutrition_to_pdf(story, nutrients)
        
        # Usa spazio ridotto se ci sono molti pasti
        space_after_meal = 6 if is_compact else 10
        story.append(Spacer(1, space_after_meal))
    
    def _add_weekly_diet_nutrition_to_pdf(self, story: list, nutrients: Dict[str, Any]):
        """
        Aggiunge i valori nutrizionali di un pasto della weekly diet al PDF.
        
        Args:
            story: Lista degli elementi del PDF
            nutrients: Dati nutrizionali del pasto
        """
        if not nutrients:
            return
        
        # Estrai i valori nutrizionali con diverse possibili chiavi
        kcal = nutrients.get('kcal', nutrients.get('kcal_totali', 0))
        proteine = nutrients.get('proteine', nutrients.get('proteine_g', 0))
        carboidrati = nutrients.get('carboidrati', nutrients.get('carboidrati_g', 0))
        grassi = nutrients.get('grassi', nutrients.get('grassi_g', 0))
        
        # Se ci sono valori nutrizionali, mostrali
        if any([kcal, proteine, carboidrati, grassi]):
            nutrition_data = [
                ['Calorie', 'Proteine', 'Carboidrati', 'Grassi'],
                [f"{kcal} kcal", f"{proteine}g", f"{carboidrati}g", f"{grassi}g"]
            ]
            
            nutrition_table = Table(nutrition_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            nutrition_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#fef9e7')),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            story.append(nutrition_table)
    
    def _sort_meals_by_time(self, meals_data):
        """
        Ordina i pasti in base all'ordine cronologico corretto: colazione, spuntino mattutino, 
        pranzo, spuntino pomeridiano, cena, spuntino serale.
        
        Args:
            meals_data: Lista dei pasti non ordinati
            
        Returns:
            list: Lista dei pasti ordinati cronologicamente
        """
        if not meals_data:
            return []
        
        # Definisce l'ordine cronologico dei pasti
        meal_order = {
            'colazione': 1,
            'breakfast': 1,
            'prima_colazione': 1,
            
            'spuntino_mattutino': 2,
            'spuntino_mattina': 2,
            'spuntino_del_mattino': 2,
            'merenda_mattutina': 2,
            'snack_mattutino': 2,
            'break_mattutino': 2,
            
            'pranzo': 3,
            'lunch': 3,
            'pasto_principale': 3,
            
            'spuntino_pomeridiano': 4,
            'spuntino_pomeriggio': 4,
            'spuntino_del_pomeriggio': 4,
            'merenda': 4,
            'merenda_pomeridiana': 4,
            'snack_pomeridiano': 4,
            'break_pomeridiano': 4,
            
            'cena': 5,
            'dinner': 5,
            'secondo_pasto': 5,
            
            'spuntino_serale': 6,
            'merenda_serale': 6,
            'snack_serale': 6,
        }
        
        def get_meal_priority(meal):
            """Calcola la priorità di ordinamento per un pasto"""
            nome_pasto = meal.get('nome_pasto', '').lower().strip()
            
            # Normalizza il nome rimuovendo spazi e caratteri speciali
            nome_normalizzato = nome_pasto.replace(' ', '_').replace('-', '_')
            
            # Cerca corrispondenza diretta
            if nome_normalizzato in meal_order:
                return meal_order[nome_normalizzato]
            
            # Ricerca parziale con parole chiave
            if 'colazione' in nome_pasto or 'breakfast' in nome_pasto:
                return 1
            elif ('spuntino' in nome_pasto or 'merenda' in nome_pasto or 'snack' in nome_pasto) and \
                 ('mattut' in nome_pasto or 'mattina' in nome_pasto):
                return 2
            elif 'pranzo' in nome_pasto or 'lunch' in nome_pasto:
                return 3
            elif ('spuntino' in nome_pasto or 'merenda' in nome_pasto or 'snack' in nome_pasto) and \
                 ('pomer' in nome_pasto or 'pomeriggio' in nome_pasto):
                return 4
            elif 'cena' in nome_pasto or 'dinner' in nome_pasto:
                return 5
            elif ('spuntino' in nome_pasto or 'merenda' in nome_pasto or 'snack' in nome_pasto) and \
                 ('seral' in nome_pasto or 'sera' in nome_pasto):
                return 6
            else:
                # Pasti non riconosciuti vanno alla fine
                return 999
        
        # Ordina i pasti in base alla priorità cronologica
        return sorted(meals_data, key=get_meal_priority)
    
    def _add_document_footer(self, story: list):
        """
        Aggiunge il footer del documento con informazioni aggiuntive.
        
        Args:
            story: Lista degli elementi del PDF
        """
        story.append(PageBreak())
        
        # Titolo note
        story.append(Paragraph("📋 Note Importanti e Protocolli Nutrizionali", self.styles['CustomSectionTitle']))
        story.append(Spacer(1, 15))
        
        # Sezione Idratazione e Timing Pasti
        story.append(Paragraph("💧 Protocollo Idratazione e Timing Pasti", self.styles['CustomSubTitle']))
        hydration_notes = [
            "• <b>Idratazione:</b> Assumere almeno 30-35ml di acqua per kg di peso corporeo al giorno (circa 2-2.5L per un adulto di 70kg).",
            "• <b>Timing idratazione:</b> Bere 1-2 bicchieri d'acqua al risveglio, un bicchiere 30 minuti prima di ogni pasto e distribuire il resto durante la giornata.",
            "• <b>Distanziamento pasti:</b> Mantenere sempre almeno 1 ora e 30 minuti di distanza tra i pasti principali e gli spuntini per ottimizzare digestione e assorbimento.",
            "• <b>Ultima assunzione:</b> Evitare liquidi abbondanti 2 ore prima del sonno per non compromettere il riposo notturno."
        ]
        
        for note in hydration_notes:
            story.append(Paragraph(note, self.styles['CustomBodyText']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 15))
        
        # Sezione Basi Scientifiche
        story.append(Paragraph("🔬 Basi Scientifiche e Metodologie", self.styles['CustomSubTitle']))
        scientific_notes = [
            "• <b>Fabbisogno energetico:</b> Calcolato secondo l'equazione di Harris-Benedict validata da studi internazionali.",
            "• <b>Dispendio sportivo:</b> Basato su ricerche dell'International Centre for Sport Studies (ICSS).",
            "• <b>Fabbisogno proteico:</b> Determinato secondo le linee guida Project Invictus e letteratura scientifica specifica.",
            "• <b>Distribuzione macronutrienti:</b> Conforme ai LARN (Livelli di Assunzione di Riferimento di Nutrienti) italiani.",
            "• <b>Valutazione ultraprocessati:</b> Classificazione secondo il sistema NOVA dell'Università di San Paolo.",
            "• <b>Database nutrizionale:</b> Valori CREA (Consiglio per la ricerca in agricoltura) - tabelle ufficiali italiane."
        ]
        
        for note in scientific_notes:
            story.append(Paragraph(note, self.styles['CustomBodyText']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 15))
        
        # Sezione Sistema e Personalizzazione
        story.append(Paragraph("🤖 Sistema e Personalizzazione", self.styles['CustomSubTitle']))
        system_notes = [
            "• I dati nutrizionali sono estratti automaticamente dalle conversazioni con l'assistente NutriCoach usando tecnologia AI avanzata.",
            "• Il piano è personalizzato in base alle tue caratteristiche fisiche, livello di attività e obiettivi.",
            "• Per modifiche o aggiornamenti, continua la conversazione con l'assistente nutrizionale.",
            "• Questo documento è stato generato automaticamente e riflette le informazioni disponibili al momento della creazione."
        ]
        
        for note in system_notes:
            story.append(Paragraph(note, self.styles['CustomBodyText']))
            story.append(Spacer(1, 6))
        
        # Footer finale
        story.append(Spacer(1, 20))
        footer_text = f"Documento generato da NutriCoach il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}"
        story.append(Paragraph(footer_text, self.styles['CustomCenteredText'])) 