from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

from common import add_common_csv_args, dataframe_to_markdown, ensure_reports_dir, read_csv_chunks, resolve_input_path, write_markdown


def recommendation(column: str, missing_rate: float) -> str:
    lower = column.lower()
    if missing_rate == 0:
        return "Rien a faire"
    if any(token in lower for token in ["name", "nom", "legal", "organisme"]):
        return "Garder, creer un indicateur is_missing si necessaire"
    if any(token in lower for token in ["city", "ville"]):
        return "Remplacer par Unknown si pertinent"
    if any(token in lower for token in ["amount", "montant"]):
        return "Verifier le type numerique, imputer par mediane si justifie"
    if missing_rate < 0.05:
        return "Imputation simple"
    if missing_rate <= 0.40:
        return "Imputation + colonne is_missing"
    if missing_rate <= 0.70:
        return "Evaluer l'utilite metier de la colonne"
    return "Suppression possible sauf valeur metier importante"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calcule les valeurs manquantes par colonne.")
    add_common_csv_args(parser)
    parser.add_argument("--reports-dir", default="reports", help="Dossier de sortie des rapports.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_path = resolve_input_path(args.input)
    reports_dir = ensure_reports_dir(args.reports_dir)
    missing = Counter()
    total_rows = 0
    columns: list[str] | None = None

    for chunk in read_csv_chunks(input_path, encoding=args.encoding, sep=args.sep, chunksize=args.chunksize):
        if columns is None:
            columns = list(chunk.columns)
        total_rows += len(chunk)
        missing.update(chunk.isna().sum().to_dict())
        stripped_empty = chunk.astype("string").apply(lambda col: col.str.strip().eq("").sum())
        missing.update(stripped_empty.to_dict())

    report = pd.DataFrame(
        [
            {
                "colonne": column,
                "valeurs_manquantes": int(missing[column]),
                "total_lignes": total_rows,
                "pourcentage_manquant": round((int(missing[column]) / total_rows) * 100, 2) if total_rows else 0,
                "recommandation": recommendation(column, int(missing[column]) / total_rows if total_rows else 0),
            }
            for column in (columns or [])
        ]
    ).sort_values("pourcentage_manquant", ascending=False)

    report.to_csv(reports_dir / "missing_values_report.csv", index=False)
    write_markdown(
        reports_dir / "02_missing_values.md",
        "Valeurs manquantes",
        [("Resume", f"- Lignes analysees: `{total_rows}`"), ("Colonnes", dataframe_to_markdown(report))],
    )


if __name__ == "__main__":
    main()
