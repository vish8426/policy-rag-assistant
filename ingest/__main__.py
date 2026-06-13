"""CLI entrypoint:  python -m ingest  [--dry-run] [--backend st|hash]

Builds (or rebuilds) the Chroma index from the policy corpus.
"""
from __future__ import annotations

import argparse
import json
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the policy corpus into Chroma.")
    parser.add_argument(
        "--backend",
        default="st",
        choices=["st", "hash"],
        help="Embedding backend: 'st' = all-MiniLM-L6-v2 (default), 'hash' = deterministic test embedder.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only; do not embed or write to Chroma.",
    )
    args = parser.parse_args()

    # Import here so --help works without heavy deps installed.
    from .pipeline import run

    t0 = time.time()
    stats = run(backend=args.backend, dry_run=args.dry_run)
    stats["seconds"] = round(time.time() - t0, 2)

    print(json.dumps(stats, indent=2))
    if args.dry_run:
        print("\nDry run complete (no embeddings written).")
    else:
        print(f"\nIndexed {stats['stored']} chunks into "
              f"collection '{stats['collection']}' at {stats['chroma_dir']}.")


if __name__ == "__main__":
    main()
