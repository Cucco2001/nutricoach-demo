"""
Utilità per la gestione delle immagini nell'applicazione.
"""

import base64
import os


def get_base64_image(image_path):
    """
    Converte un'immagine in base64 per l'embedding nell'HTML.
    
    Args:
        image_path: Percorso dell'immagine
        
    Returns:
        str: Stringa base64 dell'immagine o None se non trovata
    """
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        else:
            print(f"[WARNING] Immagine non trovata: {image_path}")
            return None
    except Exception as e:
        print(f"[ERROR] Errore nel caricamento dell'immagine: {e}")
        return None


def get_image_html(image_path, width=None, height=None, alt=""):
    """
    Genera il tag HTML img con l'immagine in base64.
    
    Args:
        image_path: Percorso dell'immagine
        width: Larghezza dell'immagine (opzionale)
        height: Altezza dell'immagine (opzionale)
        alt: Testo alternativo
        
    Returns:
        str: Tag HTML img o stringa vuota se l'immagine non è trovata
    """
    base64_img = get_base64_image(image_path)
    
    if base64_img:
        style = ""
        if width:
            style += f"width: {width}px; "
        if height:
            style += f"height: {height}px; "
        
        return f'<img src="data:image/png;base64,{base64_img}" style="{style}" alt="{alt}">'
    
    return "" 