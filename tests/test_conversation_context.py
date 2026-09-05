import unittest

from brain.conversation_engine import ConversationEngine


class ConversationContextTest(unittest.TestCase):
    def test_infer_topic_recognizes_portfolio_and_voice(self):
        engine = ConversationEngine.__new__(ConversationEngine)
        self.assertEqual(engine._infer_topic("improve the animation on my portfolio"), "portfolio")
        self.assertEqual(engine._infer_topic("fix the voice bug"), "voice")

    def test_follow_up_only_when_context_is_missing(self):
        engine = ConversationEngine.__new__(ConversationEngine)
        self.assertTrue(engine._should_ask_follow_up("can you improve it", ""))
        self.assertFalse(engine._should_ask_follow_up("can you improve the portfolio animation", "portfolio"))


if __name__ == "__main__":
    unittest.main()
