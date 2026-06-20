from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

from common import (
    dataframe_to_markdown,
    ensure_reports_dir,
    read_csv_chunks,
    resolve_entity_column,
    resolve_input_path,
    write_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Produit le rapport final du projet.")
    parser.add_argument("--raw-input", default=None)
    parser.add_argument("--clean-input", default="data/processed/fichier_nettoye.csv")
    parser.add_argument("--mapping", default="reports/entity_cleaning_mapping.csv")
    parser.add_argument("--duplicates-report", default="reports/duplicates_report.csv")
    parser.add_argument("--encoding", default=None)
    parser.add_argument("--sep", default=None)
    parser.add_argument("--chunksize", type=int, default=100_000)
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--org-column", "--column", dest="org_column", default=None)
    return parser


def summarize_file(
    path: Path,
    org_column: str | None,
    encoding: str | None,
    sep: str | None,
    chunksize: int,
) -> dict[str, object]:
    total_rows = 0
    columns: list[str] | None = None
    missing = Counter()
    unique_org_values: set[str] = set()

    for chunk in read_csv_chunks(path, encoding=encoding, sep=sep, chunksize=chunksize):
        if columns is None:
            columns = list(chunk.columns)
        if org_column and org_column in chunk.columns:
            entity_column = org_column
        elif not org_column:
            clean_candidates = [column for column in chunk.columns if column.endswith("_clean")]
            entity_column = clean_candidates[0] if clean_candidates else resolve_entity_column(chunk.columns, None)
        else:
            entity_column = resolve_entity_column(chunk.columns, org_column)
        total_rows += len(chunk)
        missing.update(chunk.isna().sum().to_dict())
        stripped_empty = chunk.astype("string").apply(lambda col: col.str.strip().eq("").sum())
        missing.update(stripped_empty.to_dict())
        unique_org_values.update(
            value for value in chunk[entity_column].dropna().astype("string").str.strip().tolist() if value
        )

    missing_df = pd.DataFrame(
        [
            {"colonne": column, "valeurs_manquantes": int(missing[column])}
            for column in (columns or [])
        ]
    ).sort_values("valeurs_manquantes", ascending=False)
    return {
        "total_rows": total_rows,
        "columns": columns or [],
        "missing_df": missing_df,
        "unique_org_count": len(unique_org_values),
    }


def main() -> None:
    args = build_parser().parse_args()
    reports_dir = ensure_reports_dir(args.reports_dir)
    raw_input = resolve_input_path(args.raw_input)
    clean_input = Path(args.clean_input)
    if not clean_input.exists():
        raise SystemExit(f"Erreur: fichier nettoye introuvable: {clean_input}. Lancez 06_clean_file.py.")

    raw_summary = summarize_file(raw_input, args.org_column, args.encoding, args.sep, args.chunksize)
    clean_summary = summarize_file(clean_input, f"{args.org_column}_clean" if args.org_column else None, args.encoding, args.sep, args.chunksize)

    duplicates_count = 0
    duplicates_path = Path(args.duplicates_report)
    if duplicates_path.exists():
        duplicates = pd.read_csv(duplicates_path)
        duplicates_count = int(duplicates["duplicate_count"].sub(1).sum()) if "duplicate_count" in duplicates else len(duplicates)

    corrections_appliquees = 0
    corrections_a_verifier = 0
    mapping_path = Path(args.mapping)
    if mapping_path.exists():
        mapping = pd.read_csv(mapping_path, dtype="string").fillna("")
        corrections_appliquees = int(mapping["status"].str.lower().eq("accepted").sum()) if "status" in mapping else 0
        corrections_a_verifier = int(mapping["status"].str.lower().eq("review").sum()) if "status" in mapping else 0

    overview = pd.DataFrame(
        [
            {"indicateur": "lignes_fichier_original", "valeur": raw_summary["total_rows"]},
            {"indicateur": "colonnes_fichier_original", "valeur": len(raw_summary["columns"])},
            {"indicateur": "doublons_detectes", "valeur": duplicates_count},
            {"indicateur": "organismes_uniques_avant", "valeur": raw_summary["unique_org_count"]},
            {"indicateur": "organismes_uniques_apres", "valeur": clean_summary["unique_org_count"]},
            {"indicateur": "corrections_acceptees", "valeur": corrections_appliquees},
            {"indicateur": "corrections_a_verifier", "valeur": corrections_a_verifier},
        ]
    )

    write_markdown(
        reports_dir / "final_summary.md",
        "Rapport final",
        [
            ("Indicateurs", dataframe_to_markdown(overview)),
            ("Valeurs manquantes par colonne", dataframe_to_markdown(raw_summary["missing_df"], max_rows=200)),
            (
                "Limites du nettoyage",
                "\n".join(
                    [
                        "- Les scores fuzzy ne prouvent pas qu'il s'agit de la meme entite.",
                        "- Les statuts `review` ne sont pas appliques automatiquement.",
                        "- Les corrections doivent etre confirmees avec le contexte metier: adresse, ville, province, code postal, numero d'entreprise.",
                    ]
                ),
            ),
            (
                "Recommandations",
                "\n".join(
                    [
                        "- Valider manuellement les lignes `review` du mapping.",
                        "- Ajouter des identifiants officiels d'organismes si disponibles.",
                        "- Conserver la colonne originale et auditer regulierement le rapport de nettoyage.",
                    ]
                ),
            ),
        ],
    )


if __name__ == "__main__":
    main()
