from __future__ import annotations

import argparse
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from common import (
    dataframe_to_markdown,
    ensure_reports_dir,
    positive_int,
    read_csv_chunks,
    read_csv_sample,
    write_markdown,
)


DEFAULT_INPUT = Path("data/raw/fichier_original.csv")
DEFAULT_COLUMN = "recipient_legal_name"
DEFAULT_REPORT = "organization_variants_report.csv"


def normalize_text(value: Any) -> str:
    """Normalise une valeur texte pour comparer des noms d'organisations."""
    if pd.isna(value):
        return ""

    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[.]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def decide(score: float) -> str:
    if score >= 95:
        return "accepted"
    if score >= 80:
        return "review"
    return "rejected"


def resolve_target_columns(
    input_path: Path,
    column_arg: str | None,
    encoding: str | None,
    sep: str | None,
    text_only: bool,
) -> list[str]:
    """Retourne une colonne demandee ou toutes les colonnes du CSV."""
    sample = read_csv_sample(input_path, encoding=encoding, sep=sep, nrows=5)
    if column_arg:
        if column_arg in sample.columns:
            return [column_arg]
        raise SystemExit(f"Erreur: colonne introuvable: {column_arg}")

    if not text_only:
        return list(sample.columns)

    text_columns = []
    for column in sample.columns:
        values = sample[column].dropna().astype("string").str.strip()
        if values.empty:
            continue
        numeric_rate = pd.to_numeric(values, errors="coerce").notna().mean()
        if numeric_rate < 0.8:
            text_columns.append(column)
    if not text_columns:
        raise SystemExit("Erreur: aucune colonne textuelle detectee. Utilisez --column NOM_DE_COLONNE.")
    return text_columns


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detecte les variantes similaires de noms d'organisations sans modifier le CSV source."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"CSV source. Defaut: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--column",
        "--org-column",
        dest="column",
        default=None,
        help="Colonne unique a analyser. Si absent, toutes les colonnes textuelles du CSV sont analysees.",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Analyser seulement les colonnes detectees comme textuelles. Sans cette option, toutes les colonnes sont analysees.",
    )
    parser.add_argument("--encoding", default=None, help="Encodage CSV. Detecte si absent.")
    parser.add_argument("--sep", default=None, help="Separateur CSV. Detecte si absent.")
    parser.add_argument("--chunksize", type=positive_int, default=100_000)
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--max-values", type=positive_int, default=20_000)
    return parser


def count_values(
    input_path: Path,
    column: str,
    *,
    encoding: str | None,
    sep: str | None,
    chunksize: int,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for chunk in read_csv_chunks(input_path, encoding=encoding, sep=sep, chunksize=chunksize):
        if column not in chunk.columns:
            raise SystemExit(f"Erreur: colonne introuvable dans un chunk: {column}")
        values = chunk[column].dropna().astype("string").str.strip()
        counts.update(value for value in values if value)
    return counts


def count_values_for_columns(
    input_path: Path,
    columns: list[str],
    *,
    encoding: str | None,
    sep: str | None,
    chunksize: int,
) -> dict[str, Counter[str]]:
    counts_by_column = {column: Counter() for column in columns}
    for chunk in read_csv_chunks(input_path, encoding=encoding, sep=sep, chunksize=chunksize):
        missing = [column for column in columns if column not in chunk.columns]
        if missing:
            raise SystemExit(f"Erreur: colonnes introuvables dans un chunk: {', '.join(missing)}")
        for column in columns:
            values = chunk[column].dropna().astype("string").str.strip()
            counts_by_column[column].update(value for value in values if value)
    return counts_by_column


def build_report(counts: Counter[str], max_values: int, column_name: str | None = None) -> pd.DataFrame:
    try:
        from rapidfuzz import fuzz, process
    except ModuleNotFoundError as exc:
        raise SystemExit("Erreur: rapidfuzz est requis. Installez les dependances avec: pip install -r requirements.txt") from exc

    rows = [
        {
            "original_value": original,
            "normalized_value": normalize_text(original),
            "count": count,
        }
        for original, count in counts.most_common(max_values)
    ]
    values_df = pd.DataFrame(rows)
    if values_df.empty:
        return pd.DataFrame(
            columns=[
                "column_name",
                "original_value",
                "normalized_value",
                "suggested_group",
                "similarity_score",
                "count",
                "decision",
            ]
        )

    # Le representant d'un groupe est la valeur originale la plus frequente pour une forme normalisee.
    representatives = (
        values_df.sort_values(["normalized_value", "count"], ascending=[True, False])
        .groupby("normalized_value", dropna=False)["original_value"]
        .first()
        .to_dict()
    )
    normalized_group_sizes = values_df.groupby("normalized_value", dropna=False)["original_value"].nunique().to_dict()
    normalized_choices = [value for value in values_df["normalized_value"].unique().tolist() if value]

    report_rows: list[dict[str, object]] = []
    for row in values_df.itertuples(index=False):
        normalized_value = row.normalized_value
        if not normalized_value:
            suggested_group = ""
            score = 0.0
        elif normalized_group_sizes.get(normalized_value, 0) > 1:
            suggested_group = representatives.get(normalized_value, "")
            score = 100.0
        else:
            other_choices = [choice for choice in normalized_choices if choice != normalized_value]
            match = process.extractOne(normalized_value, other_choices, scorer=fuzz.WRatio) if other_choices else None
            matched_normalized = match[0] if match else ""
            score = float(match[1]) if match else 0.0
            suggested_group = representatives.get(matched_normalized, "")

        report_rows.append(
            {
                "column_name": column_name or "",
                "original_value": row.original_value,
                "normalized_value": normalized_value,
                "suggested_group": suggested_group,
                "similarity_score": round(score, 2),
                "count": int(row.count),
                "decision": decide(score),
            }
        )

    return pd.DataFrame(report_rows).sort_values(
        ["column_name", "decision", "suggested_group", "similarity_score", "count"],
        ascending=[True, True, True, False, False],
    )


def build_reports_for_columns(counts_by_column: dict[str, Counter[str]], max_values: int) -> pd.DataFrame:
    reports = [
        build_report(counts, max_values, column_name=column)
        for column, counts in counts_by_column.items()
    ]
    if not reports:
        return pd.DataFrame(
            columns=[
                "column_name",
                "original_value",
                "normalized_value",
                "suggested_group",
                "similarity_score",
                "count",
                "decision",
            ]
        )
    return pd.concat(reports, ignore_index=True)


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Erreur: fichier introuvable: {input_path}")

    reports_dir = ensure_reports_dir(args.reports_dir)
    target_columns = resolve_target_columns(input_path, args.column, args.encoding, args.sep, args.text_only)
    counts_by_column = count_values_for_columns(
        input_path,
        target_columns,
        encoding=args.encoding,
        sep=args.sep,
        chunksize=args.chunksize,
    )
    report = build_reports_for_columns(counts_by_column, args.max_values)

    output_path = reports_dir / DEFAULT_REPORT
    report.to_csv(output_path, index=False)
    write_markdown(
        reports_dir / "04_detect_text_variants.md",
        "Variantes de noms d'organisations",
        [
            (
                "Resume",
                "\n".join(
                    [
                        f"- Fichier source: `{input_path}`",
                        f"- Colonnes analysees: `{', '.join(target_columns)}`",
                        f"- Valeurs distinctes: `{sum(len(counts) for counts in counts_by_column.values())}`",
                        f"- Rapport CSV: `{output_path}`",
                        "- Le fichier original n'est pas modifie.",
                    ]
                ),
            ),
            ("Apercu", dataframe_to_markdown(report.head(50))),
        ],
    )


if __name__ == "__main__":
    main()
