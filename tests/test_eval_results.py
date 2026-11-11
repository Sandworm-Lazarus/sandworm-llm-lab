"""Authored synthetic checks; these do not evaluate a live model."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval_results.py"
SPEC = importlib.util.spec_from_file_location("eval_results", SCRIPT)
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)


def case(identifier="sample", answer="Expected", expected_ids=None, prediction_ids=None,
         expected_abstain=False, predicted_abstain=False):
    return {
        "id": identifier,
        "expected": {"answers": [] if expected_abstain else ["Expected"],
                     "citations": [] if expected_ids is None else expected_ids,
                     "abstain": expected_abstain},
        "prediction": {"answer": answer,
                       "citations": [] if prediction_ids is None else prediction_ids,
                       "abstain": predicted_abstain},
    }


def document(*cases):
    return {"schema_version": 1, "cases": list(cases)}


class EvaluationTests(unittest.TestCase):
    def test_normalization_is_explicit_not_semantic(self):
        self.assertEqual(evaluator.normalize_answer("  cafe\u0301\t\n test  "), "café test")
        self.assertEqual(evaluator.normalize_answer("คำ\u200bไทย"), "คำ\u200bไทย")
        self.assertEqual(evaluator.normalize_answer("Ａ"), "Ａ")
        sample = case(answer="expected")
        self.assertFalse(evaluator.evaluate(document(sample))["cases"][0]["answer_exact_match"])

    def test_authored_answer_aliases_are_supported(self):
        sample = case(answer="Second")
        sample["expected"]["answers"].append("Second")
        self.assertTrue(evaluator.evaluate(document(sample))["cases"][0]["answer_exact_match"])

    def test_citation_metrics_use_counts_and_micro_denominators(self):
        data = document(case("first", expected_ids=["a", "b"], prediction_ids=["a", "extra"]),
                        case("second", expected_ids=["c"], prediction_ids=["c"]))
        result = evaluator.evaluate(data)
        self.assertEqual(result["citation_micro"], {
            "true_positive": 2, "false_positive": 1, "false_negative": 1,
            "precision": 0.666667, "recall": 0.666667, "f1": 0.666667})
        self.assertEqual(result["cases"][0]["citations"]["recall"], 0.5)

    def test_empty_citation_denominators_are_null(self):
        result = evaluator.evaluate(document(case()))["citation_micro"]
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["recall"])
        self.assertIsNone(result["f1"])
        missing = evaluator.evaluate(document(case(expected_ids=["source"])))
        self.assertIsNone(missing["citation_micro"]["precision"])
        self.assertEqual(missing["citation_micro"]["recall"], 0.0)
        self.assertEqual(missing["citation_micro"]["f1"], 0.0)
        extra = evaluator.evaluate(document(case(prediction_ids=["invented"])))
        self.assertEqual(extra["citation_micro"]["precision"], 0.0)
        self.assertIsNone(extra["citation_micro"]["recall"])

    def test_empty_dataset_does_not_claim_perfect_accuracy(self):
        result = evaluator.evaluate(document())
        self.assertEqual(result["cases_total"], 0)
        self.assertIsNone(result["answer_exact_match"]["rate"])
        self.assertIsNone(result["abstention_accuracy"]["rate"])
        self.assertNotIn("NaN", evaluator.render_metrics(result))

    def test_correct_and_inconsistent_abstentions(self):
        good = case("good", answer="", expected_abstain=True, predicted_abstain=True)
        inconsistent = case("inconsistent", answer="claimed answer", expected_abstain=True,
                            predicted_abstain=True)
        cited = case("cited", answer="", expected_abstain=True, predicted_abstain=True,
                     prediction_ids=["source"])
        empty_answer = case("empty", answer="")
        result = evaluator.evaluate(document(good, inconsistent, cited, empty_answer))
        self.assertEqual(result["abstention_accuracy"], {"correct": 1, "total": 4, "rate": 0.25})
        self.assertEqual(result["answer_exact_match"], {"correct": 0, "total": 1, "rate": 0.0})
        self.assertIsNone(next(x for x in result["cases"] if x["id"] == "good")["answer_exact_match"])

    def test_predictions_marked_abstain_cannot_earn_answer_match(self):
        result = evaluator.evaluate(document(case(predicted_abstain=True)))
        self.assertFalse(result["cases"][0]["answer_exact_match"])
        self.assertFalse(result["cases"][0]["abstention_correct"])

    def test_order_is_deterministic_and_input_is_not_mutated(self):
        data = document(case("z"), case("a"))
        saved = copy.deepcopy(data)
        first = evaluator.render_metrics(evaluator.evaluate(data))
        data["cases"].reverse()
        second = evaluator.render_metrics(evaluator.evaluate(data))
        self.assertEqual(first, second)
        data["cases"].reverse()
        self.assertEqual(data, saved)

    def test_strict_schema_duplicate_ids_and_citations(self):
        invalid = [None, [], {}, {"schema_version": True, "cases": []},
                   {"schema_version": 1, "cases": [], "typo": True},
                   document(case(), case())]
        for path, value in [("id", "contains space"), ("prediction", {}), ("expected", None)]:
            sample = case()
            sample[path] = value
            invalid.append(document(sample))
        duplicate = case(prediction_ids=["a", "a"])
        invalid.append(document(duplicate))
        duplicate = case(expected_ids=["a", "a"])
        invalid.append(document(duplicate))
        for value in invalid:
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(evaluator.EvaluationError):
                    evaluator.evaluate(value)

    def test_invalid_expectations_and_types_are_rejected(self):
        invalid = []
        for answers in [[], [" "], ["Expected", " Expected "], [2]]:
            sample = case()
            sample["expected"]["answers"] = answers
            invalid.append(document(sample))
        sample = case(expected_abstain=True)
        sample["expected"]["answers"] = ["Not empty"]
        invalid.append(document(sample))
        sample = case(expected_abstain=True, expected_ids=["source"])
        invalid.append(document(sample))
        sample = case()
        sample["prediction"]["abstain"] = 0
        invalid.append(document(sample))
        sample = case(answer="\ud800")
        invalid.append(document(sample))
        for value in invalid:
            with self.assertRaises(evaluator.EvaluationError):
                evaluator.evaluate(value)

    def test_duplicate_json_keys_and_numeric_extensions_are_rejected(self):
        for raw in (b'{"schema_version":1,"schema_version":1,"cases":[]}',
                    b'{"schema_version":NaN,"cases":[]}',
                    b'{"schema_version":1.0,"cases":[]}',
                    b'{"schema_version":'+b'9'*100+b',"cases":[]}', b'{} {}', b'\xff'):
            with self.subTest(raw=raw[:25]):
                with self.assertRaises(evaluator.EvaluationError):
                    evaluator.parse_document(raw)

    def test_input_depth_byte_case_and_string_budgets(self):
        for raw in (b" " * (evaluator.MAX_BYTES + 1), b"[" * 1000 + b"]" * 1000):
            with self.assertRaises(evaluator.EvaluationError):
                evaluator.parse_document(raw)
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate({"schema_version": 1, "cases": [case()] * (evaluator.MAX_CASES + 1)})
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate(document(case(answer="ก" * (evaluator.MAX_TEXT_BYTES // 3 + 1))))
        sample = case(answer="[brackets] {inside quoted text}")
        self.assertEqual(evaluator.parse_document(json.dumps(document(sample)).encode()), document(sample))

    def test_alias_citation_and_cumulative_api_budgets(self):
        sample = case()
        sample["expected"]["answers"] = [str(i) for i in range(evaluator.MAX_ANSWERS + 1)]
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate(document(sample))
        sample = case(prediction_ids=["source-" + str(i) for i in range(evaluator.MAX_CITATIONS + 1)])
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate(document(sample))
        broad = []
        for i in range(8):
            sample = case("large-" + str(i))
            sample["expected"]["answers"] = [str(j).zfill(4) + "x" * (evaluator.MAX_TEXT_BYTES - 4)
                                                for j in range(evaluator.MAX_ANSWERS)]
            broad.append(sample)
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate(document(*broad))


class CLITests(unittest.TestCase):
    def run_cli(self, *args, raw=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], input=raw,
                              capture_output=True, timeout=10)

    def test_golden_example_and_expected_metrics(self):
        source = ROOT / "examples" / "eval-cases.json"
        golden = ROOT / "examples" / "eval-results.json"
        result = self.run_cli("--input", source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, golden.read_bytes())
        metrics = json.loads(result.stdout)
        self.assertEqual(metrics["answer_exact_match"], {"correct": 3, "total": 4, "rate": 0.75})
        self.assertEqual(metrics["abstention_accuracy"], {"correct": 5, "total": 6, "rate": 0.833333})
        self.assertEqual(metrics["citation_micro"]["precision"], 0.6)
        self.assertEqual(metrics["citation_micro"]["recall"], 0.75)
        self.assertEqual(self.run_cli("--input", source, "--check", golden).returncode, 0)
        self.assertNotIn("ค่าจัดส่ง", result.stdout.decode("utf-8"))

    def test_stdin_and_golden_mismatch(self):
        raw = json.dumps(document(case())).encode()
        result = self.run_cli(raw=raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "golden.json"
            path.write_text("{}\n", encoding="utf-8")
            mismatch = self.run_cli("--check", path, raw=raw)
            self.assertEqual((mismatch.returncode, mismatch.stdout), (1, b""))

    def test_invalid_input_and_arguments_do_not_echo_payloads(self):
        marker = b"synthetic-private-answer"
        result = self.run_cli(raw=b'{"'+marker+b'":NaN}')
        self.assertEqual((result.returncode, result.stdout), (2, b""))
        self.assertNotIn(marker, result.stderr)
        invalid_argument = self.run_cli("--synthetic-private-answer")
        self.assertEqual((invalid_argument.returncode, invalid_argument.stdout), (2, b""))
        self.assertNotIn(marker, invalid_argument.stderr)

    def test_missing_file_uses_distinct_io_status_without_echoing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("--input", Path(directory) / "synthetic-private-path")
        self.assertEqual((result.returncode, result.stdout), (3, b""))
        self.assertNotIn(b"synthetic-private-path", result.stderr)


if __name__ == "__main__":
    unittest.main()
