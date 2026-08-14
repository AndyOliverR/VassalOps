import json
import unittest

from pydantic import ValidationError

from src.execution.structured_llm import (
    LoopDecisionModel,
    PlannerPlan,
    call_ollama_json,
    complete_structured,
)


class TestPlannerPlan(unittest.TestCase):
    def test_valid_steps(self):
        plan = PlannerPlan.model_validate(
            {"steps": [{"type": "speak_log", "payload": "hi"}, {"type": "focus_window", "payload": "Notepad"}]}
        )
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].type, "speak_log")

    def test_rejects_unknown_type(self):
        with self.assertRaises(ValidationError):
            PlannerPlan.model_validate({"steps": [{"type": "shell_exec", "payload": "rm"}]})


class TestCompleteStructured(unittest.TestCase):
    def test_invalid_then_valid_on_retry(self):
        calls = {"n": 0, "prompts": []}

        def model(prompt):
            calls["n"] += 1
            calls["prompts"].append(prompt)
            if calls["n"] == 1:
                return "not json"
            return {"action": "final", "payload": "Done."}

        result = complete_structured("Reply JSON", LoopDecisionModel, model, max_retries=1)
        self.assertTrue(result.ok)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.data.kind, "final")
        self.assertEqual(result.data.payload, "Done.")
        self.assertIn("VALIDATION ERROR", calls["prompts"][1])

    def test_planner_retry_then_valid(self):
        calls = {"n": 0}

        def model(_prompt):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"steps": [{"type": "shell_exec", "payload": "nope"}]}
            return {"steps": [{"type": "speak_log", "payload": "ok"}]}

        result = complete_structured("plan", PlannerPlan, model, max_retries=1)
        self.assertTrue(result.ok)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.data.steps[0].type, "speak_log")

    def test_still_invalid_after_retry(self):
        result = complete_structured(
            "Reply JSON",
            LoopDecisionModel,
            lambda _p: "still broken",
            max_retries=1,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.attempts, 2)


class TestCallOllamaJson(unittest.TestCase):
    def test_parses_response_field(self):
        class FakeResp:
            def json(self):
                return {"response": json.dumps({"action": "final", "payload": "hi"})}

        def post(url, json=None, timeout=None):
            self.assertIn("/api/generate", url)
            self.assertEqual(json["format"], "json")
            return FakeResp()

        out = call_ollama_json(
            "hello",
            host="127.0.0.1",
            port=11434,
            model_name="test",
            post=post,
        )
        self.assertEqual(out["payload"], "hi")


if __name__ == "__main__":
    unittest.main()
