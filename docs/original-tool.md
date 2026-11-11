# Recorded answer and citation evaluation

This original Python 3.9+ standard-library utility evaluates **already-recorded
predictions** against authored expectations. It makes no model, API or network
calls. Use it to catch regressions in a small retrieval/RAG fixture before
spending time on a larger semantic evaluation.

The included Thai/English examples are fabricated by this project. Their
predictions are deliberately authored to include mistakes. The resulting numbers
are **fixture outcomes**, not benchmark scores for any model.

## Run

Run from the focused LLM Lab repository's root. In the collection hub, first
change directory with `cd originals/llm-lab`:

```bash
python3 scripts/eval_results.py --input examples/eval-cases.json
python3 scripts/eval_results.py --input examples/eval-cases.json --check examples/eval-results.json
python3 -m unittest discover -s tests -p 'test_eval_results.py' -v
```

Without `--input`, read UTF-8 JSON from stdin. Successful stdout contains only
deterministic JSON metrics, with cases sorted by ID and numeric rates rounded to
six decimal places. Reports contain case IDs and scores; they omit original
answers and citation contents. Exit status `0` means evaluation/check succeeded,
**not that predictions were correct**. Status `1` means golden metrics differ,
`2` means invalid input/arguments, and `3` means I/O failed. Golden checking is an
exact byte comparison with the formatted output produced by this version.

Do not redirect output to the input file. Use a separate results path, review
changes to expectations and predictions, then intentionally refresh the golden
file when justified.

## Input contract

```json
{
  "schema_version": 1,
  "cases": [
    {
      "id": "thai-shipping",
      "expected": {
        "answers": ["ค่าจัดส่ง 25 บาท"],
        "citations": ["shipping-policy"],
        "abstain": false
      },
      "prediction": {
        "answer": "ค่าจัดส่ง 25 บาท",
        "citations": ["shipping-policy"],
        "abstain": false
      }
    }
  ]
}
```

All shown fields are required and unknown fields are rejected. IDs use ASCII
letters initially, followed by letters, digits, `.`, `_`, `:`, or `-`, up to 80
characters. Case IDs are unique. Citation IDs are unique within each list; the
evaluator rejects duplicates instead of silently changing denominators. Citation
IDs are case-sensitive and are never normalized as prose.

Answerable expectations require one or more accepted answer strings. An expected
abstention requires `answers: []`, `citations: []`, and `abstain: true`.
Predictions can be wrong or internally inconsistent; those cases receive
nonmatching outcomes rather than being silently removed from the dataset.

## Scoring and empty sets

| Measure | Definition |
| --- | --- |
| Answer exact match | For answerable cases only, compare the normalized prediction with any authored accepted answer. A prediction marked `abstain` cannot earn a match. |
| Answer normalization | Unicode NFC, then collapse Unicode whitespace and trim ends. Preserve letter case, punctuation, digits and zero-width characters. No translation, Thai word segmentation, synonym inference or semantic judgment. |
| Abstention accuracy | Expected and predicted flags must agree. A declared abstention must have an empty normalized answer and no citations. A declared answer must have a nonempty normalized answer. |
| Citation precision | `TP / (TP + FP)`, where TP is the intersection of expected and predicted ID sets. |
| Citation recall | `TP / (TP + FN)`. Missing required citations count as FN; extra citations count as FP. |
| Citation F1 | `2TP / (2TP + FP + FN)`. Compute directly from counts. |
| Aggregate citations | Sum counts across **all cases**, including expected abstentions, then calculate micro metrics. Do not average case percentages. |

Any zero denominator is `null`, not NaN, zero, or perfect accuracy. Thus a case
with no expected or predicted citations has null precision/recall/F1; a missing
required citation has null precision, zero recall and zero F1. An extra citation
when none is expected has zero precision, null recall and zero F1. Empty datasets
are accepted and yield zero counts with null rates; they do not demonstrate
success. Answer exact match is null per expected-abstention case and excluded
from the answer-accuracy denominator.

Scores are independent: correct citation IDs do not repair a wrong answer, and
an answer can match exactly while carrying an unsupported extra citation. No
arbitrary overall score is invented from these measures.

## Authored example corpus and expected outcomes

These statements are fictional evaluation content, not current product facts:

- `shipping-policy`: ค่าจัดส่ง 25 บาท
- `cache-guide`: Cache expires after 10 minutes.
- `hours`: เปิดบริการ 09:00–17:00
- `palette`: Colour: blue. / Color: blue. are explicitly accepted aliases.
- No source establishes any private account detail or location of the fictional
  NPC เมืองดาวม่วง.

The six example predictions include one wrong cache duration, one missing
citation, two extra citations and one failure to abstain. Expected aggregates:
answer exact match **3/4**, valid abstention behavior **5/6**, citation micro
precision **3/5**, recall **3/4**, F1 **6/9**. The golden JSON records those
deterministic fixture results.

## Limits and strict parsing

- Maximum serialized input: 2 MiB of UTF-8 bytes; maximum parser nesting: 16.
- At most 1,000 cases, 20 accepted answers per case, and 100 citation IDs per list.
- Each answer is at most 16,384 UTF-8 bytes. The Python API also bounds cumulative
  input string bytes to 2 MiB, even for pre-parsed objects.
- Reject duplicate JSON keys, floating-point input, NaN/Infinity, excessive integer
  text, malformed JSON and invalid Unicode. This schema needs only integer
  `schema_version`, strings, booleans, arrays and objects.
- Invalid inputs produce no partial metrics. Diagnostics use fixed messages
  rather than echoing answer text, rejected arguments or file paths.

Exact match cannot establish semantic correctness, and citation-ID overlap cannot
establish entailment, document authenticity or completeness. Validate the
authored expectations and separately review source support. These fixtures do
not measure ASR/TTS quality, live-model accuracy, provider latency, cost, prompt
injection resilience or production performance. No external corpus, third-party
model output or upstream package is bundled.
