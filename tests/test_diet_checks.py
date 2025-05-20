import unittest
from utils.diet_checks import validate_diet_plan

class TestDietChecks(unittest.TestCase):
    def test_validate_diet_plan(self):
        # Test case 1: Valid diet plan with acceptable ultra-processed food ratios
        valid_diet = {
            "colazione": [
                ("mela", 150),
                ("yogurt_naturale", 200),
                ("muesli", 50)
            ],
            "pranzo": [
                ("pollo", 150),
                ("riso_integrale", 100),
                ("insalata_mista", 200)
            ],
            "cena": [
                ("pesce_spada", 150),
                ("patate", 200),
                ("zucchine", 150)
            ]
        }
        
        is_valid, message = validate_diet_plan(valid_diet)
        self.assertTrue(is_valid)
        self.assertIn("✓ Validazione completata con successo!", message)
        
        # Test case 2: Invalid diet plan with too many ultra-processed foods
        invalid_diet = {
            "colazione": [
                ("cornflakes", 100),
                ("latte", 200),
                ("biscotti", 100)
            ],
            "pranzo": [
                ("hamburger", 150),
                ("patatine_fritte", 200),
                ("coca_cola", 330)
            ],
            "cena": [
                ("pizza_margherita", 300),
                ("gelato", 200)
            ]
        }
        
        is_valid, message = validate_diet_plan(invalid_diet)
        self.assertFalse(is_valid)
        self.assertIn("✗ La dieta contiene troppi alimenti ultra-processati", message)
        
        # Test case 3: Diet plan with invalid food names
        invalid_food_diet = {
            "colazione": [
                ("invalid_food", 100),
                ("latte", 200)
            ]
        }
        
        is_valid, message = validate_diet_plan(invalid_food_diet)
        self.assertFalse(is_valid)
        self.assertIn("Errore nel pasto", message)

if __name__ == '__main__':
    unittest.main() 