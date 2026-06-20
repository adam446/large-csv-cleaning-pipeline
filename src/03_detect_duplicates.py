from __future__ import annotations

import argparse
import hashlib
from collections import Counter

import pandas as pd

from common import (
    add_common_csv_args,
    dataframe_to_markdown,
    ensure_reports_dir,
    read_csv_chunks,
    require_columns,
    resolve_input_path,
    resolve_entity_column,
    write_markdown,
)


def row_hashes(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    values = df[columns].astype("string").fillna("").agg("\x1f".join, axis=1)
    return values.map(lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detecte les doublons exacts ou par cles.")
    add_common_csv_args(parser)
    parser.add_argument("--reports-dir", default="reports", help="Dossier de sortie des rapports.")
    parser.add_argument(
        "--key-columns",
        default="",
        help="Colonnes cles separees par des virgules. Si vide, toutes les colonnes sont utilisees.",
    )
    parser.add_argument("--org-column", default=None, help="Colonne organisme pour les doublons probables.")
    return parser


def available_subset(columns: list[str], candidates: list[str]) -> list[str]:
    return [column for column in candidates if column in columns]


def main() -> None:
    args = build_parser().parse_args()
    input_path = resolve_input_path(args.input)
    reports_dir = ensure_reports_dir(args.reports_dir)
    counts_by_rule: dict[str, Counter[str]] = {}
    examples_by_rule: dict[str, dict[str, dict[str, str]]] = {}
    columns: list[str] | None = None
    total_rows = 0

    for chunk in read_csv_chunks(input_path, encoding=args.encoding, sep=args.sep, chunksize=args.chunksize):
        if columns is None:
            columns = list(chunk.columns)
        org_column = resolve_entity_column(chunk.columns, args.org_column)
        exact_columns = [c.strip() for c in args.key_columns.split(",") if c.strip()] or list(chunk.columns)
        ref_columns = available_subset(list(chunk.columns), ["ref_number", "reference_number", "id"])
        org_date_amount = [org_column, *available_subset(list(chunk.columns), ["date", "amount", "montant"])]
        org_city_postal = [org_column, *available_subset(list(chunk.columns), ["recipient_city", "ville", "city", "code_postal", "postal_code"])]
        rules = {
            "exact_row": exact_columns,
            "same_reference": ref_columns,
            "same_organization_date_amount": org_date_amount,
            "same_organization_city_postal": org_city_postal,
        }
        total_rows += len(chunk)
        for rule_name, selected_columns in rules.items():
            if len(selected_columns) < 1:
                continue
            require_columns(chunk, selected_columns)
            counts_by_rule.setdefault(rule_name, Counter())
            examples_by_rule.setdefault(rule_name, {})
            hashes = row_hashes(chunk, selected_columns)
            counts_by_rule[rule_name].update(hashes)
            for digest, (_, row) in zip(hashes, chunk.iterrows(), strict=False):
                if digest not in examples_by_rule[rule_name]:
                    examples_by_rule[rule_name][digest] = {
                        "duplicate_type": rule_name,
                        **{column: str(row[column]) for column in selected_columns},
                    }

    duplicate_rows = []
    for rule_name, counts in counts_by_rule.items():
        for digest, count in counts.items():
            if count > 1:
                duplicate_rows.append(
                    {"hash": digest, "duplicate_count": count, **examples_by_rule[rule_name][digest]}
                )
    report_columns = ["duplicate_type", "hash", "duplicate_count", *(columns or [])]
    report = pd.DataFrame(duplicate_rows, columns=report_columns).sort_values("duplicate_count", ascending=False)
    report.to_csv(reports_dir / "duplicates_report.csv", index=False)

    duplicate_groups = len(report)
    duplicate_extra_rows = int(report["duplicate_count"].sub(1).sum()) if not report.empty else 0
    write_markdown(
        reports_dir / "03_detect_duplicates.md",
        "Doublons",
        [
            (
                "Resume",
                "\n".join(
                    [
                        f"- Lignes analysees: `{total_rows}`",
                        f"- Groupes en doublon: `{duplicate_groups}`",
                        f"- Lignes excedentaires: `{duplicate_extra_rows}`",
                    ]
                ),
            ),
            ("Exemples", dataframe_to_markdown(report.head(50))),
        ],
    )


if __name__ == "__main__":
    main()
