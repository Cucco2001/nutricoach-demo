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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


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
            fontSize=16,
            textColor=HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=10,
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
        
        # Crea il documento PDF
        doc = SimpleDocTemplate(
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
        
        # Sezioni principali
        self._add_caloric_needs_section(story, extracted_data)
        self._add_macros_section(story, extracted_data)
        self._add_daily_plan_section(story, extracted_data)
        self._add_registered_meals_section(story, extracted_data)
        
        # Footer informativo
        self._add_document_footer(story)
        
        # Genera il PDF
        doc.build(story)
        
        # Restituisci i bytes del PDF
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _load_user_nutritional_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati nutrizionali dell'utente dal file JSON.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            dict: Dati nutrizionali estratti o None se non trovati
        """
        user_file_path = f"user_data/{user_id}.json"
        
        if not os.path.exists(user_file_path):
            return None
            
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        return user_data.get("nutritional_info_extracted", {})
    
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
        if "caloric_needs" not in extracted_data:
            return
        
        caloric_data = extracted_data["caloric_needs"]
        
        # Titolo sezione
        story.append(Paragraph("🔥 Fabbisogno Energetico Giornaliero", self.styles['CustomSectionTitle']))
        
        # Tabella con i valori calorici
        caloric_table_data = [
            ['Parametro', 'Valore', 'Descrizione'],
            ['Metabolismo Basale (BMR)', f"{caloric_data.get('bmr', 0)} kcal", 'Energia per le funzioni vitali'],
            ['Fabbisogno Base', f"{caloric_data.get('fabbisogno_base', 0)} kcal", 'Con attività quotidiana'],
            ['Dispendio Sportivo', f"{caloric_data.get('dispendio_sportivo', 0)} kcal", 'Calorie dall\'attività sportiva'],
            ['Fabbisogno Totale', f"{caloric_data.get('fabbisogno_totale', 0)} kcal", 'Calorie totali giornaliere']
        ]
        
        caloric_table = Table(caloric_table_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        caloric_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(caloric_table)
        
        # Informazioni aggiuntive
        additional_info = []
        laf = caloric_data.get('laf_utilizzato', 'N/A')
        additional_info.append(f"<b>Fattore Attività (LAF):</b> {laf}")
        
        aggiustamento = caloric_data.get('aggiustamento_obiettivo', 0)
        if aggiustamento != 0:
            simbolo = "+" if aggiustamento > 0 else ""
            additional_info.append(f"<b>Aggiustamento Obiettivo:</b> {simbolo}{aggiustamento} kcal")
        
        if additional_info:
            story.append(Spacer(1, 10))
            for info in additional_info:
                story.append(Paragraph(info, self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 20))
    
    def _add_macros_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione dei macronutrienti.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if "macros_total" not in extracted_data:
            return
        
        macros_data = extracted_data["macros_total"]
        
        # Titolo sezione
        story.append(Paragraph("🥗 Distribuzione Calorica Giornaliera", self.styles['CustomSectionTitle']))
        
        # Tabella macronutrienti
        macros_table_data = [
            ['Macronutriente', 'Grammi', 'Calorie', 'Percentuale'],
            ['Proteine', f"{macros_data.get('proteine_g', 0)}g", f"{macros_data.get('proteine_kcal', 0)} kcal", f"{macros_data.get('proteine_percentuale', 0)}%"],
            ['Carboidrati', f"{macros_data.get('carboidrati_g', 0)}g", f"{macros_data.get('carboidrati_kcal', 0)} kcal", f"{macros_data.get('carboidrati_percentuale', 0)}%"],
            ['Grassi', f"{macros_data.get('grassi_g', 0)}g", f"{macros_data.get('grassi_kcal', 0)} kcal", f"{macros_data.get('grassi_percentuale', 0)}%"]
        ]
        
        macros_table = Table(macros_table_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1*inch])
        macros_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(macros_table)
        
        # Totali aggiuntivi
        story.append(Spacer(1, 10))
        totals_info = []
        
        fibre = macros_data.get('fibre_g', 0)
        if fibre > 0:
            totals_info.append(f"<b>Fibre giornaliere:</b> {fibre}g")
        
        kcal_totali = macros_data.get('kcal_totali', 0)
        totals_info.append(f"<b>Calorie Totali:</b> {kcal_totali} kcal")
        
        for info in totals_info:
            story.append(Paragraph(info, self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 20))
    
    def _add_daily_plan_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione del piano pasti giornaliero.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if "daily_macros" not in extracted_data:
            return
        
        daily_data = extracted_data["daily_macros"]
        
        # Titolo sezione
        story.append(Paragraph("🍽️ Piano Pasti Giornaliero", self.styles['CustomSectionTitle']))
        
        num_pasti = daily_data.get('numero_pasti', 0)
        story.append(Paragraph(f"<b>Piano giornaliero:</b> {num_pasti} pasti", self.styles['CustomBodyText']))
        story.append(Spacer(1, 10))
        
        if "distribuzione_pasti" not in daily_data:
            return
        
        # Tabella distribuzione pasti
        distribuzione_pasti = daily_data["distribuzione_pasti"]
        meal_table_data = [['Pasto', 'Calorie', '% del Totale', 'Proteine', 'Carboidrati', 'Grassi']]
        
        for pasto_nome, pasto_data in distribuzione_pasti.items():
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
        
        meal_table = Table(meal_table_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 0.7*inch])
        meal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]))
        
        story.append(meal_table)
        story.append(Spacer(1, 20))
    
    def _add_registered_meals_section(self, story: list, extracted_data: Dict[str, Any]):
        """
        Aggiunge la sezione dei pasti registrati.
        
        Args:
            story: Lista degli elementi del PDF
            extracted_data: Dati nutrizionali estratti
        """
        if "registered_meals" not in extracted_data or not extracted_data["registered_meals"]:
            return
        
        meals_data = extracted_data["registered_meals"]
        
        # Titolo sezione
        story.append(Paragraph("👨‍🍳 Ricette e Pasti Creati", self.styles['CustomSectionTitle']))
        
        for i, meal in enumerate(meals_data):
            nome_pasto = meal.get('nome_pasto', 'Pasto').title()
            
            # Sottotitolo del pasto
            story.append(Paragraph(f"🍽️ {nome_pasto}", self.styles['CustomSubTitle']))
            
            # Ingredienti
            if "alimenti" in meal and meal["alimenti"]:
                story.append(Paragraph("<b>Ingredienti:</b>", self.styles['CustomBodyText']))
                
                ingredients_data = [['Alimento', 'Quantità', 'Stato', 'Misura Casalinga', 'Metodo Cottura']]
                
                for alimento in meal["alimenti"]:
                    nome = alimento.get('nome_alimento', 'N/A')
                    quantita = alimento.get('quantita_g', 'N/A')
                    stato = alimento.get('stato', 'N/A')
                    misura = alimento.get('misura_casalinga', 'N/A')
                    metodo = alimento.get('metodo_cottura', 'N/A')
                    
                    ingredients_data.append([nome, f"{quantita}g", stato, misura, metodo])
                
                ingredients_table = Table(ingredients_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1.2*inch, 1*inch])
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
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
                ]))
                
                story.append(ingredients_table)
                story.append(Spacer(1, 10))
            
            # Totali nutrizionali
            if "totali_pasto" in meal:
                totali = meal["totali_pasto"]
                
                totals_data = [
                    ['Calorie Totali', 'Proteine Totali', 'Carboidrati Totali', 'Grassi Totali'],
                    [
                        f"{totali.get('kcal_totali', 0)} kcal",
                        f"{totali.get('proteine_totali', 0)}g",
                        f"{totali.get('carboidrati_totali', 0)}g",
                        f"{totali.get('grassi_totali', 0)}g"
                    ]
                ]
                
                totals_table = Table(totals_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
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
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
                ]))
                
                story.append(totals_table)
            
            # Separatore tra pasti (tranne l'ultimo)
            if i < len(meals_data) - 1:
                story.append(Spacer(1, 15))
        
        story.append(Spacer(1, 20))
    
    def _add_document_footer(self, story: list):
        """
        Aggiunge il footer del documento con informazioni aggiuntive.
        
        Args:
            story: Lista degli elementi del PDF
        """
        story.append(PageBreak())
        
        # Titolo note
        story.append(Paragraph("📋 Note Importanti", self.styles['CustomSectionTitle']))
        
        # Note sul sistema
        notes = [
            "• I dati nutrizionali sono estratti automaticamente dalle conversazioni con l'assistente NutriCoach usando tecnologia AI avanzata.",
            "• Tutti i valori sono calcolati secondo le linee guida LARN (Livelli di Assunzione di Riferimento di Nutrienti).",
            "• I calcoli del fabbisogno energetico utilizzano l'equazione di Harris-Benedict modificata.",
            "• Il piano è personalizzato in base alle tue caratteristiche fisiche, livello di attività e obiettivi.",
            "• Per modifiche o aggiornamenti, continua la conversazione con l'assistente nutrizionale.",
            "• Questo documento è stato generato automaticamente e riflette le informazioni disponibili al momento della creazione."
        ]
        
        for note in notes:
            story.append(Paragraph(note, self.styles['CustomBodyText']))
            story.append(Spacer(1, 8))
        
        # Footer finale
        story.append(Spacer(1, 20))
        footer_text = f"Documento generato da NutriCoach il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}"
        story.append(Paragraph(footer_text, self.styles['CustomCenteredText'])) 