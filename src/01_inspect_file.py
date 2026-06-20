from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import (
    add_common_csv_args,
    count_lines,
    dataframe_to_markdown,
    ensure_reports_dir,
    read_csv_sample,
    resolve_input_path,
    resolve_csv_options,
    write_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspecte rapidement un gros fichier CSV.")
    add_common_csv_args(parser)
    parser.add_argument("--reports-dir", default="reports", help="Dossier de sortie des rapports.")
    parser.add_argument("--sample-rows", type=int, default=1_000, help="Nombre de lignes a echantillonner.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_path = resolve_input_path(args.input)
    reports_dir = ensure_reports_dir(args.reports_dir)
    encoding, sep = resolve_csv_options(input_path, args.encoding, args.sep)
    sample = read_csv_sample(input_path, encoding=encoding, sep=sep, nrows=args.sample_rows)

    column_report = pd.DataFrame(
        {
            "column": sample.columns,
            "sample_dtype": [str(dtype) for dtype in sample.dtypes],
            "sample_non_null": [int(sample[column].notna().sum()) for column in sample.columns],
            "sample_unique": [int(sample[column].nunique(dropna=True)) for column in sample.columns],
        }
    )
    column_report.to_csv(reports_dir / "01_columns_report.csv", index=False)
    sample.head(50).to_csv(reports_dir / "01_sample_rows.csv", index=False)

    total_lines = count_lines(input_path)
    numeric_columns = sample.apply(pd.to_numeric, errors="coerce").columns[
        sample.apply(pd.to_numeric, errors="coerce").notna().mean() > 0.8
    ].tolist()
    date_columns = [column for column in sample.columns if "date" in column.lower()]
    text_columns = [column for column in sample.columns if column not in numeric_columns]
    sections = [
        (
            "1. Apercu general",
            "\n".join(
                [
                    f"- Chemin: `{input_path}`",
                    f"- Encodage: `{encoding}`",
                    f"- Separateur: `{sep}`",
                    f"- Taille: `{input_path.stat().st_size}` octets",
                    f"- Nombre de lignes estime: `{max(total_lines - 1, 0)}`",
                    f"- Nombre de colonnes: `{len(sample.columns)}`",
                ]
            ),
        ),
        ("2. Colonnes", dataframe_to_markdown(column_report)),
        ("3. Colonnes numeriques possibles", "\n".join(f"- {column}" for column in numeric_columns) or "_Aucune._"),
        ("4. Colonnes textuelles possibles", "\n".join(f"- {column}" for column in text_columns) or "_Aucune._"),
        ("5. Colonnes de date possibles", "\n".join(f"- {column}" for column in date_columns) or "_Aucune._"),
        ("6. Apercu des premieres lignes", dataframe_to_markdown(sample.head(20))),
    ]
    write_markdown(reports_dir / "eda_report.md", "EDA Report", sections)


if __name__ == "__main__":
    main()
