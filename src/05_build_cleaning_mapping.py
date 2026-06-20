from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

import pandas as pd

from common import dataframe_to_markdown, ensure_reports_dir, write_markdown


VARIANTS_REPORT = Path("reports/organization_variants_report.csv")
MAPPING_REPORT = Path("reports/entity_cleaning_mapping.csv")


def uqam_rule(original_value: str, current_clean_value: str, current_status: str) -> tuple[str, str, str]:
    text = unicodedata.normalize("NFKD", str(original_value).upper())
    text = "".join(char for char in text if not unicodedata.combining(char))
    normalized = "".join(char for char in text if char.isalnum())
    accepted_aliases = {
        "UQAM",
        "UQAM",
        "UNIVERSITEDUQUEBECAMONTREAL",
        "UNIVERSITEDUQUEBECAMONTREAL",
    }
    review_aliases = {"AQAM", "QAM"}
    spaced = " ".join(text.replace(".", " ").split())

    if normalized in accepted_aliases or spaced == "U Q A M":
        return "UQAM", "accepted", "variante evidente ou nom complet de l'UQAM"
    if normalized in review_aliases:
        return str(original_value), "review", "forte similarite avec UQAM mais validation requise"
    return current_clean_value, current_status, "decision issue du rapport de similarite"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cree un mapping de correction a partir du rapport de variantes.")
    parser.add_argument("--input", default=str(VARIANTS_REPORT), help="Rapport organization_variants_report.csv.")
    parser.add_argument("--output", default=str(MAPPING_REPORT), help="Fichier mapping a produire.")
    parser.add_argument("--reports-dir", default="reports")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Erreur: rapport introuvable: {input_path}. Lancez 04_detect_text_variants.py.")

    reports_dir = ensure_reports_dir(args.reports_dir)
    variants = pd.read_csv(input_path, dtype="string").fillna("")
    required = {"original_value", "suggested_group", "similarity_score", "decision"}
    missing = required - set(variants.columns)
    if missing:
        raise SystemExit(f"Erreur: colonnes absentes du rapport de variantes: {', '.join(sorted(missing))}")

    rows = []
    for row in variants.itertuples(index=False):
        status = str(row.decision).strip().lower()
        clean_value = str(row.suggested_group).strip() if status == "accepted" else str(row.original_value).strip()
        reason = f"score de similarite {row.similarity_score}"
        clean_value, status, special_reason = uqam_rule(str(row.original_value), clean_value, status)
        if special_reason != "decision issue du rapport de similarite":
            reason = special_reason
        rows.append(
            {
                "column_name": getattr(row, "column_name", ""),
                "original_value": row.original_value,
                "clean_value": clean_value,
                "status": status,
                "reason": reason,
            }
        )

    mapping = pd.DataFrame(rows)
    subset = ["column_name", "original_value"] if "column_name" in mapping.columns else ["original_value"]
    mapping = mapping.drop_duplicates(subset=subset, keep="first")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(output_path, index=False)
    write_markdown(
        reports_dir / "cleaning_decisions.md",
        "Decisions de nettoyage",
        [
            (
                "Regles",
                "\n".join(
                    [
                        "- `accepted`: correction applicable automatiquement.",
                        "- `review`: correction probable mais non appliquee.",
                        "- `rejected`: correction refusee.",
                    ]
                ),
            ),
            ("Mapping", dataframe_to_markdown(mapping.head(100))),
        ],
    )


if __name__ == "__main__":
    main()
