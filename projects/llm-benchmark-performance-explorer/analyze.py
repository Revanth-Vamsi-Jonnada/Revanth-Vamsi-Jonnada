"""Reproducible analysis for the supplied LLM benchmark score dataset."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

REQUIRED = {"model_id", "model_name", "organization", "release_date", "benchmark", "benchmark_type", "score", "max_score", "score_pct"}

def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing columns: {sorted(REQUIRED - set(reader.fieldnames or []))}")
        rows = list(reader)
    seen = set()
    for line, row in enumerate(rows, start=2):
        key = (row["model_id"], row["benchmark"])
        if key in seen:
            raise ValueError(f"Duplicate model/benchmark pair at CSV line {line}: {key}")
        seen.add(key)
        score, maximum, pct = (float(row[column]) for column in ("score", "max_score", "score_pct"))
        if maximum <= 0 or not 0 <= score <= maximum:
            raise ValueError(f"Invalid score bounds at CSV line {line}")
        if abs(pct - score / maximum * 100) > 0.02:
            raise ValueError(f"score_pct mismatch at CSV line {line}")
    return rows

def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def summarize(rows: list[dict[str, str]]):
    groups = {}
    for row in rows:
        groups.setdefault(row["benchmark"], []).append(row)
    leaders, coverage = [], []
    model_total = len({row["model_id"] for row in rows})
    for benchmark, group in sorted(groups.items()):
        ordered = sorted(group, key=lambda row: (-float(row["score_pct"]), row["model_name"]))
        for rank, row in enumerate(ordered[:3], start=1):
            leaders.append({"benchmark": benchmark, "rank": rank, "model_id": row["model_id"], "model_name": row["model_name"], "organization": row["organization"], "release_date": row["release_date"], "score": row["score"], "max_score": row["max_score"], "score_pct": row["score_pct"]})
        coverage.append({"benchmark": benchmark, "benchmark_type": group[0]["benchmark_type"], "models_reported": len(group), "models_total": model_total, "coverage_pct": round(len(group) / model_total * 100, 2), "score_min": min(float(row["score"]) for row in group), "score_max": max(float(row["score"]) for row in group)})
    return leaders, coverage

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/benchmark_scores.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    rows = load_rows(args.input)
    leaders, coverage = summarize(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "benchmark_leaders_top3.csv", list(leaders[0]), leaders)
    write_csv(args.output_dir / "benchmark_coverage.csv", list(coverage[0]), coverage)
    print(f"Validated {len(rows):,} rows, {len({r['model_id'] for r in rows})} models, {len({r['benchmark'] for r in rows})} benchmarks and {len({r['organization'] for r in rows})} organizations.")
    print(f"Wrote leaders and coverage summaries to {args.output_dir}.")

if __name__ == "__main__":
    main()

