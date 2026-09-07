"""
Convert the MoinSystems AI RAG dataset workbook (RAG_Knowledge sheet) into
the canonical JSONL format used by the ingestion pipeline.

Usage:
    python scripts/convert_dataset.py path/to/dataset.xlsx

Writes: data/raw/moinsystems_rag_dataset_v2.jsonl

This is a one-time / re-run-on-source-update step, separate from
ingest_rag.py — it only reshapes the source, it never talks to the
database or an embedding provider.
"""
import json
import sys
from pathlib import Path

import pandas as pd

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "moinsystems_rag_dataset_v2.jsonl"
DATASET_VERSION = "v2"


def split_list_field(value: object) -> list[str]:
    """'about, company, software house' -> ['about', 'company', 'software house']"""
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def main(xlsx_path: str) -> None:
    df = pd.read_excel(xlsx_path, sheet_name="RAG_Knowledge")

    records = []
    for _, row in df.iterrows():
        record = {
            "id": str(row["ID"]).strip(),
            "title": str(row["Title"]).strip(),
            "category": str(row["Category"]).strip(),
            "tags": split_list_field(row["Tags"]),
            "intents": split_list_field(row["Intents"]),
            "text": str(row["Embedding Text"]).strip(),
            "metadata": {
                "dataset_version": DATASET_VERSION,
                "data_status": str(row["Data Status"]).strip(),
                "source_basis": (
                    str(row["Source Basis"]).strip()
                    if pd.notna(row["Source Basis"])
                    else None
                ),
            },
        }
        records.append(record)

    ids = [r["id"] for r in records]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise SystemExit(f"Duplicate IDs found in source — fix before ingesting: {duplicates}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/convert_dataset.py path/to/dataset.xlsx")
    main(sys.argv[1])
