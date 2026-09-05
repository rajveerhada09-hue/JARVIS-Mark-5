import unittest

from brain.brain import JarvisBrain


class PlannerFlowTest(unittest.TestCase):
    def test_planner_classifies_workspace_request(self):
        brain = JarvisBrain.__new__(JarvisBrain)
        plan = brain._build_plan("open my workspace")
        self.assertEqual(plan["category"], "workspace")
        self.assertEqual(plan["kind"], "multi_step")

    def test_planner_classifies_long_term_goal(self):
        brain = JarvisBrain.__new__(JarvisBrain)
        plan = brain._build_plan("I want to build a portfolio website")
        self.assertEqual(plan["category"], "goal")
        self.assertEqual(plan["kind"], "long_term")


if __name__ == "__main__":
    unittest.main()
