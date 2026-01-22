import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.services.trainer import AITrainerBrain


class TestPromptStructure(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
        self.trainer = AITrainerBrain(self.mock_db, self.mock_llm, self.mock_memory)

    def test_prompt_contains_critical_section(self):
        """Testa se a seção de Fatos Críticos é renderizada corretamente quando existem dados."""
        # Simula o input_data que será passado ao template
        # O AITrainerBrain.send_message_ai constrói a string, mas aqui vamos testar o template
        # via _get_prompt_template.
        # Como o template é construído dinamicamente na string relevant_memories,
        # precisamos testar se o output final contém os headers.

        # Simulando o que o send_message_ai faz para construir input_data
        input_data = {
            "trainer_profile": "Perfil Teste",
            "user_profile": "User Teste",
            "relevant_memories": "## 🚨 Fatos Críticos (ATENÇÃO MÁXIMA):\n- ⚠️ (01/01) Alergia a lactose",
            "chat_history_summary": "Histórico...",
            "user_message": "Oi",
        }

        # Render prompt
        template = self.trainer._get_prompt_template(input_data)
        prompt_text = template.format(**input_data)

        print(f"\n[DEBUG] Rendered Prompt:\n{prompt_text[:500]}...")

        # Assert Section Headers Exist
        self.assertIn("## 🚨 Fatos Críticos", prompt_text)
        self.assertIn("Alergia a lactose", prompt_text)

        # Validar hierarquia: Fatos críticos devem aparecer ANTES do histórico
        critical_pos = prompt_text.find("## 🚨 Fatos Críticos")
        history_pos = prompt_text.find("## 💬 Histórico")

        self.assertTrue(
            critical_pos < history_pos,
            "Fatos Críticos devem aparecer antes do Histórico",
        )


if __name__ == "__main__":
    unittest.main()
