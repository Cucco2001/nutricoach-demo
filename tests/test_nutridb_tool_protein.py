import unittest
from agent_tools.nutridb_tool import get_protein_multiplier

class TestNutriDBTool(unittest.TestCase):
    def test_single_sport_basic(self):
        """Test with a single sport, basic case"""
        sport = {
            "sport_type": "Fitness - Allenamento medio (principianti e livello intermedio)",
            "intensity": "medium"
        }
        result = get_protein_multiplier(sport)
        self.assertIsInstance(result, dict)
        self.assertIn("base", result)
        self.assertIn("description", result)

    def test_multiple_sports(self):
        """Test with multiple sports to ensure highest protein requirement is used"""
        sports = [
            {
                "sport_type": "Fitness - Allenamento medio (principianti e livello intermedio)",
                "intensity": "medium"
            },
            {
                "sport_type": "Sport di forza (es: powerlifting, sollevamento pesi, strongman)",
                "intensity": "hard"
            }
        ]
        result = get_protein_multiplier(sports)
        self.assertIsInstance(result, dict)
        self.assertIn("base", result)
        # Should use the higher protein requirement from strength sports
        self.assertGreaterEqual(result["base"], 1.6)

    def test_vegan_adjustment(self):
        """Test that vegan diet adds the correct protein supplement"""
        sport = {
            "sport_type": "Fitness - Allenamento medio (principianti e livello intermedio)",
            "intensity": "medium"
        }
        normal_result = get_protein_multiplier(sport, is_vegan=False)
        vegan_result = get_protein_multiplier(sport, is_vegan=True)
        
        # Vegan should have 0.25 more protein requirement
        self.assertAlmostEqual(vegan_result["base"], normal_result["base"] + 0.25)
        self.assertIn("vegano", vegan_result["description"].lower())

    def test_intensity_levels(self):
        """Test different intensity levels affect the protein requirements"""
        sport_type = "Sport di forza (es: powerlifting, sollevamento pesi, strongman)"
        
        easy_result = get_protein_multiplier({"sport_type": sport_type, "intensity": "easy"})
        medium_result = get_protein_multiplier({"sport_type": sport_type, "intensity": "medium"})
        hard_result = get_protein_multiplier({"sport_type": sport_type, "intensity": "hard"})
        
        # Higher intensity should require more protein
        self.assertLessEqual(easy_result["base"], medium_result["base"])
        self.assertLessEqual(medium_result["base"], hard_result["base"])

    def test_invalid_sport(self):
        """Test that invalid sport type raises ValueError"""
        sport = {
            "sport_type": "Invalid Sport",
            "intensity": "medium"
        }
        with self.assertRaises(ValueError):
            get_protein_multiplier(sport)

    def test_sedentary_case(self):
        """Test sedentary case returns appropriate values"""
        sport = {
            "sport_type": "Sedentario",
            "intensity": "medium"
        }
        result = get_protein_multiplier(sport)
        self.assertIsInstance(result, dict)
        self.assertIn("base", result)
        # Sedentary should have lower protein requirements
        self.assertLessEqual(result["base"], 1.2)

if __name__ == '__main__':
    unittest.main() 