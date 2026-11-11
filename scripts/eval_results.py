#!/usr/bin/env python3
"""Evaluate already-recorded synthetic answers and citation IDs, without models."""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 16
MAX_CASES = 1000
MAX_ANSWERS = 20
MAX_CITATIONS = 100
MAX_TEXT_BYTES = 16384
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9._:-]{0,79}\Z")


class EvaluationError(ValueError):
    """A rejected document. Messages do not contain answer payloads."""


def normalize_answer(text):
    """NFC, collapse Unicode whitespace, trim; preserve case and punctuation."""
    if type(text) is not str:
        raise EvaluationError("answer must be a string")
    if len(text) > MAX_TEXT_BYTES:
        raise EvaluationError("answer exceeds string budget")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError:
        raise EvaluationError("invalid Unicode string") from None
    if len(encoded) > MAX_TEXT_BYTES:
        raise EvaluationError("answer exceeds string budget")
    return " ".join(unicodedata.normalize("NFC", text).split())


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise EvaluationError("invalid object fields")


def _identifier(value):
    if type(value) is not str or not IDENTIFIER.fullmatch(value):
        raise EvaluationError("invalid identifier")
    return value


def _citation_ids(value):
    if type(value) is not list or len(value) > MAX_CITATIONS:
        raise EvaluationError("invalid citation list")
    identifiers = [_identifier(item) for item in value]
    if len(set(identifiers)) != len(identifiers):
        raise EvaluationError("duplicate citation identifier")
    return set(identifiers)


def _ratio(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else None


def _citation_metrics(expected, predicted):
    true_positive = len(expected & predicted)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": _ratio(true_positive, len(predicted)),
        "recall": _ratio(true_positive, len(expected)),
        "f1": _ratio(2 * true_positive, 2 * true_positive + false_positive + false_negative),
    }


def evaluate(document):
    """Return payload-free metrics for strict expected/prediction case objects.

    Citation scores measure identifier overlap, not whether the cited document
    supports the answer. Empty denominators are JSON null, never NaN or 100%.
    """
    _keys(document, {"schema_version", "cases"})
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise EvaluationError("unsupported schema version")
    cases = document["cases"]
    if type(cases) is not list or len(cases) > MAX_CASES:
        raise EvaluationError("invalid case list")
    results = []
    seen = set()
    answer_total = answer_correct = abstention_correct = 0
    true_positive = false_positive = false_negative = 0
    used_bytes = 0
    for case in cases:
        _keys(case, {"id", "expected", "prediction"})
        identifier = _identifier(case["id"])
        if identifier in seen:
            raise EvaluationError("duplicate case identifier")
        seen.add(identifier)
        expected, prediction = case["expected"], case["prediction"]
        _keys(expected, {"answers", "citations", "abstain"})
        _keys(prediction, {"answer", "citations", "abstain"})
        if type(expected["abstain"]) is not bool or type(prediction["abstain"]) is not bool:
            raise EvaluationError("abstention flags must be booleans")
        answers = expected["answers"]
        if type(answers) is not list or len(answers) > MAX_ANSWERS:
            raise EvaluationError("invalid expected answer list")
        normalized_answers = [normalize_answer(value) for value in answers]
        if (any(not value for value in normalized_answers)
                or len(set(normalized_answers)) != len(normalized_answers)):
            raise EvaluationError("empty or duplicate expected answer")
        normalized_prediction = normalize_answer(prediction["answer"])
        expected_ids = _citation_ids(expected["citations"])
        prediction_ids = _citation_ids(prediction["citations"])
        if expected["abstain"]:
            if answers or expected_ids:
                raise EvaluationError("abstention expectation must have no answer or citations")
        elif not answers:
            raise EvaluationError("answerable case requires an expected answer")
        strings = [identifier, prediction["answer"], *answers, *expected_ids, *prediction_ids]
        used_bytes += sum(len(value.encode("utf-8")) for value in strings)
        if used_bytes > MAX_BYTES:
            raise EvaluationError("document exceeds string budget")
        if prediction["abstain"]:
            valid_response = not normalized_prediction and not prediction_ids
        else:
            valid_response = bool(normalized_prediction)
        abstention_match = (expected["abstain"] == prediction["abstain"] and valid_response)
        abstention_correct += int(abstention_match)
        answer_match = None
        if not expected["abstain"]:
            answer_total += 1
            answer_match = (not prediction["abstain"]
                            and normalized_prediction in normalized_answers)
            answer_correct += int(answer_match)
        citations = _citation_metrics(expected_ids, prediction_ids)
        true_positive += citations["true_positive"]
        false_positive += citations["false_positive"]
        false_negative += citations["false_negative"]
        results.append({"id": identifier, "answer_exact_match": answer_match,
                        "abstention_correct": abstention_match, "citations": citations})
    return {
        "schema_version": 1,
        "scope": "Recorded predictions only; no model execution or semantic/citation-support assessment.",
        "normalization": "NFC; collapse Unicode whitespace and trim; preserve case, punctuation and zero-width characters.",
        "cases_total": len(results),
        "answer_exact_match": {"correct": answer_correct, "total": answer_total,
                               "rate": _ratio(answer_correct, answer_total)},
        "abstention_accuracy": {"correct": abstention_correct, "total": len(results),
                                "rate": _ratio(abstention_correct, len(results))},
        "citation_micro": {
            "true_positive": true_positive, "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": _ratio(true_positive, true_positive + false_positive),
            "recall": _ratio(true_positive, true_positive + false_negative),
            "f1": _ratio(2 * true_positive, 2 * true_positive + false_positive + false_negative),
        },
        "cases": sorted(results, key=lambda value: value["id"]),
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvaluationError("duplicate JSON object key")
        result[key] = value
    return result


def _integer(value):
    if len(value.lstrip("-")) > 20:
        raise EvaluationError("numeric input exceeds budget")
    return int(value)


def _reject_number(_value):
    raise EvaluationError("floating-point input is unsupported")


def parse_document(raw):
    """Strictly decode bounded UTF-8 JSON before schema evaluation."""
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise EvaluationError("input exceeds byte budget or has invalid type")
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        raise EvaluationError("input is not UTF-8") from None
    depth, quoted, escaped = 0, False, False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise EvaluationError("input exceeds nesting budget")
        elif character in "]}":
            depth -= 1
    try:
        return json.loads(text, object_pairs_hook=_unique_object, parse_int=_integer,
                          parse_float=_reject_number, parse_constant=_reject_number)
    except EvaluationError:
        raise
    except (ValueError, RecursionError, OverflowError):
        raise EvaluationError("malformed or unsupported JSON") from None


def render_metrics(result):
    return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "eval_results: invalid arguments; use --help\n")


def main(argv=None):
    parser = _ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="UTF-8 JSON file; default: stdin")
    parser.add_argument("--check", type=Path, help="compare metrics with an existing golden JSON file")
    args = parser.parse_args(argv)
    try:
        if args.input is not None:
            with args.input.open("rb") as handle:
                raw = handle.read(MAX_BYTES + 1)
        else:
            raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        output = render_metrics(evaluate(parse_document(raw)))
        if args.check is not None:
            with args.check.open("rb") as handle:
                golden = handle.read(4 * MAX_BYTES + 1)
            if len(golden) > 4 * MAX_BYTES or golden != output.encode("utf-8"):
                print("eval_results: golden metrics differ", file=sys.stderr)
                return 1
        else:
            sys.stdout.write(output)
        return 0
    except (EvaluationError, UnicodeError, RecursionError, OverflowError):
        print("eval_results: invalid evaluation input", file=sys.stderr)
        return 2
    except OSError:
        print("eval_results: input/output operation failed", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
