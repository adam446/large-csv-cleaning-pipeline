from __future__ import annotations

import argparse
import csv
import difflib
import re
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import chardet
import pandas as pd


DEFAULT_CHUNKSIZE = 100_000
DEFAULT_REPORTS_DIR = Path("reports")
DEFAULT_INPUT_PATH = Path("data/raw/fichier_original.csv")
DEFAULT_ENTITY_COLUMN = "recipient_legal_name"
NULL_MARKERS = {"", "nan", "none", "null", "na", "n/a", "<na>"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("La valeur doit etre un entier positif.")
    return parsed


def add_common_csv_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        default=None,
        help="Chemin du fichier CSV source. Si absent, cherche un CSV unique dans data/raw/.",
    )
    parser.add_argument("--encoding", default=None, help="Encodage CSV. Detecte si absent.")
    parser.add_argument("--sep", default=None, help="Separateur CSV. Detecte si absent.")
    parser.add_argument(
        "--chunksize",
        type=positive_int,
        default=DEFAULT_CHUNKSIZE,
        help=f"Nombre de lignes par chunk pandas. Defaut: {DEFAULT_CHUNKSIZE}.",
    )


def add_entity_column_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--org-column",
        "--column",
        dest="org_column",
        default=None,
        help=f"Colonne organisme. Defaut: `{DEFAULT_ENTITY_COLUMN}` si presente, sinon `organisme`.",
    )


def resolve_entity_column(columns: list[str] | pd.Index, requested: str | None = None) -> str:
    available = list(columns)
    if requested:
        if requested not in available:
            raise SystemExit(f"Erreur: colonne introuvable: {requested}")
        return requested
    for candidate in [DEFAULT_ENTITY_COLUMN, "organisme", "organization", "beneficiary_name"]:
        if candidate in available:
            return candidate
    raise SystemExit(
        f"Erreur: aucune colonne organisme reconnue. Utilisez --org-column. Colonnes disponibles: {', '.join(available)}"
    )


def detect_encoding(path: str | Path, sample_size: int = 200_000) -> str:
    with Path(path).open("rb") as handle:
        raw = handle.read(sample_size)
    result = chardet.detect(raw)
    return result.get("encoding") or "utf-8"


def find_single_raw_csv(raw_dir: str | Path = "data/raw") -> Path:
    default_candidate = Path(raw_dir) / DEFAULT_INPUT_PATH.name
    if default_candidate.is_file():
        return default_candidate

    candidates = sorted(path for path in Path(raw_dir).glob("*.csv") if path.is_file())
    if not candidates:
        raise FileNotFoundError(
            "Aucun fichier CSV trouve dans data/raw/. Placez votre fichier dans data/raw/ ou utilisez --input."
        )
    if len(candidates) > 1:
        names = ", ".join(str(path) for path in candidates)
        raise ValueError(f"Plusieurs CSV trouves dans data/raw/: {names}. Utilisez --input pour choisir.")
    return candidates[0]


def resolve_input_path(input_arg: str | None) -> Path:
    if input_arg:
        path = Path(input_arg)
        if not path.exists():
            raise SystemExit(f"Erreur: fichier introuvable: {path}")
        return path
    try:
        return find_single_raw_csv()
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Erreur: {exc}") from exc


def detect_separator(path: str | Path, encoding: str, sample_size: int = 20_000) -> str:
    with Path(path).open("r", encoding=encoding, errors="replace", newline="") as handle:
        sample = handle.read(sample_size)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def resolve_csv_options(path: str | Path, encoding: str | None, sep: str | None) -> tuple[str, str]:
    resolved_encoding = encoding or detect_encoding(path)
    resolved_sep = sep or detect_separator(path, resolved_encoding)
    return resolved_encoding, resolved_sep


def read_csv_chunks(
    path: str | Path,
    *,
    encoding: str | None = None,
    sep: str | None = None,
    chunksize: int = DEFAULT_CHUNKSIZE,
    dtype: str | None = "string",
    **kwargs: Any,
) -> Iterator[pd.DataFrame]:
    resolved_encoding, resolved_sep = resolve_csv_options(path, encoding, sep)
    yield from pd.read_csv(
        path,
        encoding=resolved_encoding,
        sep=resolved_sep,
        chunksize=chunksize,
        dtype=dtype,
        low_memory=False,
        **kwargs,
    )


def read_csv_sample(
    path: str | Path,
    *,
    encoding: str | None = None,
    sep: str | None = None,
    nrows: int = 1_000,
    dtype: str | None = "string",
) -> pd.DataFrame:
    resolved_encoding, resolved_sep = resolve_csv_options(path, encoding, sep)
    return pd.read_csv(
        path,
        encoding=resolved_encoding,
        sep=resolved_sep,
        nrows=nrows,
        dtype=dtype,
        low_memory=False,
    )


def ensure_reports_dir(path: str | Path) -> Path:
    reports_dir = Path(path)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def write_markdown(path: str | Path, title: str, sections: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", body.strip(), ""])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.empty:
        return "_Aucune donnee._"
    shown = df.head(max_rows)
    string_df = shown.astype("string").fillna("")
    headers = [str(column) for column in string_df.columns]
    rows = string_df.values.tolist()
    table = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(table)


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Colonnes absentes: {', '.join(missing)}")


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in NULL_MARKERS:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("?", "")
    text = re.sub(r"[._,/\\;:|()[\]{}]+", " ", text)
    text = re.sub(r"[^0-9A-Za-z&' -]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().upper()


def normalize_organization(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""

    compact = re.sub(r"[^A-Z0-9]", "", text)
    uqam_aliases = {
        "UQAM",
        "AQAM",
        "QAM",
        "UNIVERSITEDUQUEBECAMONTREAL",
        "UNIVERSITEQUEBECMONTREAL",
        "UNIVDUQUEBECAMONTREAL",
    }
    if compact in uqam_aliases:
        return "UQAM"

    replacements = {
        r"\bUNIVERSITE\b": "UNIV",
        r"\bQUEBEC\b": "QC",
        r"\bMONTREAL\b": "MTL",
        r"\bSAINTE\b": "STE",
        r"\bSAINT\b": "ST",
        r"\bINCORPOREE\b": "INC",
        r"\bINCORPORATED\b": "INC",
        r"\bLIMITED\b": "LTD",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_lines(path: str | Path) -> int:
    with Path(path).open("rb") as handle:
        return sum(1 for _ in handle)


def safe_value_counts(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").fillna("").str.strip()
    return normalized.value_counts(dropna=False)


def load_validated_mapping(path: str | Path) -> dict[str, str]:
    mapping_df = pd.read_csv(path, dtype="string").fillna("")
    if {"original_value", "clean_value", "status"}.issubset(mapping_df.columns):
        accepted = mapping_df[mapping_df["status"].str.strip().str.lower().eq("accepted")]
        accepted = accepted[accepted["clean_value"].str.strip() != ""]
        return dict(zip(accepted["original_value"], accepted["clean_value"], strict=False))

    require_columns(mapping_df, ["raw_value", "validated_clean_value", "apply"])
    apply_mask = mapping_df["apply"].str.strip().str.lower().isin({"1", "true", "yes", "y", "oui"})
    clean_mask = mapping_df["validated_clean_value"].str.strip() != ""
    valid_rows = mapping_df[apply_mask & clean_mask]
    return dict(zip(valid_rows["raw_value"], valid_rows["validated_clean_value"], strict=False))


def fuzzy_score(value: str, other: str) -> float:
    try:
        from rapidfuzz import fuzz

        return float(fuzz.WRatio(value, other))
    except ModuleNotFoundError:
        return difflib.SequenceMatcher(None, value, other).ratio() * 100


def fuzzy_extract(
    value: str,
    choices: list[str],
    *,
    score_cutoff: int,
    limit: int = 10,
) -> list[tuple[str, float]]:
    try:
        from rapidfuzz import fuzz, process

        return [(match, float(score)) for match, score, _ in process.extract(value, choices, scorer=fuzz.WRatio, score_cutoff=score_cutoff, limit=limit)]
    except ModuleNotFoundError:
        scored = [(choice, fuzzy_score(value, choice)) for choice in choices]
        return sorted(
            [(choice, score) for choice, score in scored if score >= score_cutoff],
            key=lambda item: item[1],
            reverse=True,
        )[:limit]


def fuzzy_extract_one(value: str, choices: list[str], *, score_cutoff: int) -> tuple[str, float] | None:
    matches = fuzzy_extract(value, choices, score_cutoff=score_cutoff, limit=1)
    return matches[0] if matches else None
