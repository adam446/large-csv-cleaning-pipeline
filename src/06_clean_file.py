from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from common import add_common_csv_args, add_entity_column_arg, dataframe_to_markdown, ensure_reports_dir, read_csv_chunks, resolve_entity_column, resolve_input_path, resolve_csv_options, write_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nettoie le CSV sans ecraser la colonne originale.")
    add_common_csv_args(parser)
    add_entity_column_arg(parser)
    parser.add_argument("--mapping", default="reports/entity_cleaning_mapping.csv")
    parser.add_argument("--output", default="data/processed/fichier_nettoye.csv")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Garder les doublons exacts. Par defaut, ils sont supprimes du fichier nettoye.",
    )
    return parser


def load_mapping_by_column(path: Path, fallback_column: str | None) -> dict[str, dict[str, str]]:
    mapping_df = pd.read_csv(path, dtype="string").fillna("")
    required = {"original_value", "clean_value", "status"}
    missing = required - set(mapping_df.columns)
    if missing:
        raise SystemExit(f"Erreur: colonnes absentes du mapping: {', '.join(sorted(missing))}")

    accepted = mapping_df[mapping_df["status"].str.strip().str.lower().eq("accepted")]
    accepted = accepted[accepted["clean_value"].str.strip() != ""]
    mappings: dict[str, dict[str, str]] = {}
    for row in accepted.itertuples(index=False):
        column_name = str(getattr(row, "column_name", "") or fallback_column or "").strip()
        if not column_name:
            continue
        mappings.setdefault(column_name, {})[str(row.original_value)] = str(row.clean_value)
    return mappings


def exact_row_hashes(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    values = df[columns].astype("string").fillna("").agg("\x1f".join, axis=1)
    return values.map(lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())


def main() -> None:
    args = build_parser().parse_args()
    input_path = resolve_input_path(args.input)
    mapping_path = Path(args.mapping)
    if not mapping_path.exists():
        raise SystemExit(f"Erreur: mapping introuvable: {mapping_path}. Lancez 05_build_cleaning_mapping.py.")

    reports_dir = ensure_reports_dir(args.reports_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoding, sep = resolve_csv_options(input_path, args.encoding, args.sep)

    total_rows = 0
    changed_rows = 0
    first_write = True
    created_columns: set[str] = set()
    mapping_by_column: dict[str, dict[str, str]] | None = None
    original_columns: list[str] | None = None
    seen_hashes: set[str] = set()
    duplicates_removed = 0

    for chunk in read_csv_chunks(input_path, encoding=encoding, sep=sep, chunksize=args.chunksize):
        if original_columns is None:
            original_columns = list(chunk.columns)
        if mapping_by_column is None:
            fallback_column = resolve_entity_column(chunk.columns, args.org_column)
            mapping_by_column = load_mapping_by_column(mapping_path, fallback_column)
        for column_name, mapping in mapping_by_column.items():
            if column_name not in chunk.columns:
                continue
            clean_column = f"{column_name}_clean"
            created_columns.add(clean_column)
            original = chunk[column_name].astype("string")
            chunk[clean_column] = original.map(lambda value: mapping.get(value, value))
            changed_rows += int((original.fillna("") != chunk[clean_column].fillna("")).sum())
        total_rows += len(chunk)

        if not args.keep_duplicates and original_columns:
            hashes = exact_row_hashes(chunk, original_columns)
            keep_mask = (~hashes.isin(seen_hashes)) & (~hashes.duplicated(keep="first"))
            duplicates_removed += int((~keep_mask).sum())
            seen_hashes.update(hashes[keep_mask].tolist())
            chunk = chunk.loc[keep_mask].copy()

        chunk.to_csv(output_path, mode="w" if first_write else "a", index=False, header=first_write)
        first_write = False

    report = pd.DataFrame(
        [
            {
                "total_lignes": total_rows,
                "lignes_sortie": total_rows - duplicates_removed,
                "corrections_appliquees": changed_rows,
                "doublons_exacts_supprimes": duplicates_removed,
                "colonnes_nettoyees": ", ".join(sorted(created_columns)),
                "fichier_sortie": str(output_path),
            }
        ]
    )
    write_markdown(
        reports_dir / "cleaning_execution_report.md",
        "Rapport d'execution du nettoyage",
        [
            ("Resume", dataframe_to_markdown(report)),
            (
                "Regle appliquee",
                "Seules les lignes du mapping avec `status = accepted` sont appliquees. Les statuts `review` et `rejected` restent inchanges.",
            ),
        ],
    )
    print(f"Lignes traitees: {total_rows}")
    print(f"Corrections appliquees: {changed_rows}")
    print(f"Doublons exacts supprimes: {duplicates_removed}")


if __name__ == "__main__":
    main()
