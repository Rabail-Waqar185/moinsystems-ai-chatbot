"""
Retrieval evaluation (SRS section 21): runs the 32 prepared RAG_Evaluation
queries and checks whether the expected record appears in top-3 and top-5
retrieval, per SRS's own stated evaluation method.

Usage:
    python scripts/evaluate_retrieval.py path/to/dataset.xlsx

Reads the "RAG_Evaluation" sheet (columns: ID, Query, Expected Record,
Expected Intent). Doesn't touch Expected Intent yet — intent detection
isn't built until a later milestone day; this only scores retrieval.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.retriever import retrieve  # noqa: E402

TOP_K_FOR_EVAL = 5  # retrieve 5, so we can check both top-3 and top-5 hit from one call


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/evaluate_retrieval.py path/to/dataset.xlsx")

    dataset_path = Path(sys.argv[1])
    df = pd.read_excel(dataset_path, sheet_name="RAG_Evaluation")

    total = 0
    top3_hits = 0
    top5_hits = 0
    misses: list[str] = []

    for _, row in df.iterrows():
        eval_id = row["ID"]
        query = str(row["Query"]).strip()
        expected_record = str(row["Expected Record"]).strip()
        if not query or query == "nan":
            continue

        total += 1
        results = retrieve(query, top_k=TOP_K_FOR_EVAL)
        retrieved_ids = [r.record_id for r in results]

        hit_top3 = expected_record in retrieved_ids[:3]
        hit_top5 = expected_record in retrieved_ids[:5]
        top3_hits += hit_top3
        top5_hits += hit_top5

        best_score = results[0].similarity if results else 0.0
        status = "PASS" if hit_top3 else ("TOP5" if hit_top5 else "MISS")
        print(
            f"[{status:4}] {eval_id}  {query!r}\n"
            f"        expected={expected_record}  got_top3={retrieved_ids[:3]}  "
            f"best_score={best_score:.3f}"
        )
        if not hit_top5:
            misses.append(f"{eval_id}: {query!r} (expected {expected_record}, "
                           f"got {retrieved_ids})")

    print("\n" + "=" * 60)
    print(f"Total queries evaluated: {total}")
    print(f"Top-3 accuracy: {top3_hits}/{total} ({100 * top3_hits / total:.1f}%)")
    print(f"Top-5 accuracy: {top5_hits}/{total} ({100 * top5_hits / total:.1f}%)")
    if misses:
        print(f"\n{len(misses)} complete misses (not even in top-5):")
        for m in misses:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
