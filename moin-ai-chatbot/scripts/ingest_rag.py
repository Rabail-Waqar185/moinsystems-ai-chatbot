"""
RAG ingestion pipeline (SRS section 12):
  approved JSONL source -> normalize -> validate schema/IDs
  -> (chunking, skipped: records are already atomic) -> embed
  -> upsert vector + metadata

Usage:
    python scripts/ingest_rag.py data/raw/moinsystems_rag_dataset_v2.jsonl
    python scripts/ingest_rag.py data/raw/moinsystems_rag_dataset_v2.jsonl --include-source-gap
    python scripts/ingest_rag.py data/raw/moinsystems_rag_dataset_v2.jsonl --dry-run

Idempotent: re-running with the same source upserts by `record_id`
rather than duplicating rows, so this is safe to re-run after fixing
a record or bumping the dataset version.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import KnowledgeChunk, KnowledgeDocument  # noqa: E402
from app.db.session import db_session  # noqa: E402
from app.rag.embeddings import embed_texts  # noqa: E402
from app.rag.ingestion import normalize_text  # noqa: E402

REQUIRED_FIELDS = {"id", "title", "category", "tags", "intents", "text", "metadata"}

# Categories that hold internal data-governance notes rather than content
# a public visitor should ever be shown. Excluded from the public vector
# index by default — see README for the reasoning; pass --include-source-gap
# to override.
EXCLUDED_CATEGORIES_BY_DEFAULT = {"source_gap"}


def load_and_validate(path: Path) -> list[dict]:
    records: list[dict] = []
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"Line {line_no}: invalid JSON — {e}")

            missing = REQUIRED_FIELDS - record.keys()
            if missing:
                raise SystemExit(f"Line {line_no} (id={record.get('id')}): missing fields {missing}")

            if not record["id"] or not isinstance(record["id"], str):
                raise SystemExit(f"Line {line_no}: 'id' must be a non-empty string")
            if record["id"] in seen_ids:
                raise SystemExit(f"Line {line_no}: duplicate id '{record['id']}'")
            seen_ids.add(record["id"])

            if not record["text"] or not record["text"].strip():
                raise SystemExit(f"Line {line_no} (id={record['id']}): 'text' is empty")

            records.append(record)

    if not records:
        raise SystemExit(f"No records found in {path}")
    return records


def upsert_records(records: list[dict], embeddings: list[list[float]], source_name: str, version: str) -> None:
    with db_session() as db:
        document = (
            db.query(KnowledgeDocument)
            .filter_by(source_name=source_name, version=version)
            .one_or_none()
        )
        if document is None:
            document = KnowledgeDocument(source_name=source_name, version=version, status="active")
            db.add(document)
            db.flush()  # populate document.id before use below

        inserted, updated = 0, 0
        for record, embedding in zip(records, embeddings):
            existing = db.query(KnowledgeChunk).filter_by(record_id=record["id"]).one_or_none()
            if existing is None:
                db.add(
                    KnowledgeChunk(
                        document_id=document.id,
                        record_id=record["id"],
                        title=record["title"],
                        content=record["text"],
                        embedding=embedding,
                        category=record["category"],
                        tags=record["tags"],
                        intents=record["intents"],
                        meta=record["metadata"],
                    )
                )
                inserted += 1
            else:
                existing.title = record["title"]
                existing.content = record["text"]
                existing.embedding = embedding
                existing.category = record["category"]
                existing.tags = record["tags"]
                existing.intents = record["intents"]
                existing.meta = record["metadata"]
                existing.document_id = document.id
                updated += 1

    print(f"Upserted knowledge_chunk rows — inserted: {inserted}, updated: {updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl_path", type=Path)
    parser.add_argument(
        "--include-source-gap",
        action="store_true",
        help="Include internal data-governance records (category=source_gap) in the public vector index. Off by default.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and normalize only — skip embedding generation and database writes.",
    )
    args = parser.parse_args()

    records = load_and_validate(args.jsonl_path)
    print(f"Loaded {len(records)} valid records from {args.jsonl_path}")

    if not args.include_source_gap:
        before = len(records)
        records = [r for r in records if r["category"] not in EXCLUDED_CATEGORIES_BY_DEFAULT]
        skipped = before - len(records)
        if skipped:
            print(f"Excluded {skipped} record(s) with category in {EXCLUDED_CATEGORIES_BY_DEFAULT} (use --include-source-gap to embed them)")

    for record in records:
        record["text"] = normalize_text(record["text"])

    # Write the cleaned/validated set actually used for embedding, per SRS's
    # data/raw -> data/processed distinction.
    processed_path = Path(__file__).resolve().parents[1] / "data" / "processed" / args.jsonl_path.name
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    with processed_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} normalized records to {processed_path}")

    if args.dry_run:
        print("Dry run — skipping embedding generation and database writes.")
        return

    dataset_version = records[0]["metadata"].get("dataset_version", "unknown")
    print(f"Generating embeddings for {len(records)} records (this calls the OpenAI API)...")
    embeddings = embed_texts([r["text"] for r in records])

    upsert_records(
        records,
        embeddings,
        source_name="moinsystems_rag_dataset",
        version=dataset_version,
    )
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
