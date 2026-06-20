from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
RAW_DIR = ROOT_DIR / "data" / "raw"
REPORTS_DIR = ROOT_DIR / "reports"
VARIANTS_REPORT = REPORTS_DIR / "organization_variants_report.csv"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from common import count_lines, read_csv_sample, resolve_csv_options  # noqa: E402


def load_variants_module():
    module_path = SRC_DIR / "04_detect_text_variants.py"
    spec = importlib.util.spec_from_file_location("detect_text_variants", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_raw_csv_files() -> list[Path]:
    return sorted(path for path in RAW_DIR.glob("*.csv") if path.is_file())


def choose_default_index(files: list[Path]) -> int:
    for index, path in enumerate(files):
        if path.name == "fichier_original.csv":
            return index
    return 0


def save_uploaded_file(uploaded_file) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    destination = RAW_DIR / uploaded_file.name
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def render_report_download(path: Path, label: str) -> None:
    if not path.exists():
        return
    st.download_button(
        label=label,
        data=path.read_bytes(),
        file_name=path.name,
        mime="text/csv",
        use_container_width=True,
    )


def cell_key(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def csv_value_view(sample: pd.DataFrame, report_df: pd.DataFrame, view_name: str) -> pd.DataFrame:
    if view_name == "original":
        return sample.copy()

    value_column = "normalized_value" if view_name == "normalized" else "suggested_group"
    output = sample.copy()
    for column in output.columns:
        values = output[column].dropna().astype("string").str.strip()
        if not values.empty and pd.to_numeric(values, errors="coerce").notna().mean() >= 0.8:
            continue
        if "column_name" not in report_df.columns or value_column not in report_df.columns:
            continue

        column_report = report_df[report_df["column_name"].astype("string") == column]
        if view_name == "suggested" and "decision" in column_report.columns:
            column_report = column_report[column_report["decision"].astype("string").str.lower() == "accepted"]
        lookup = {
            cell_key(row.original_value): cell_key(getattr(row, value_column))
            for row in column_report.itertuples(index=False)
        }

        def replace_value(value):
            key = cell_key(value)
            replacement = lookup.get(key, key)
            return replacement if replacement else value

        output[column] = output[column].map(replace_value)
    return output


def main() -> None:
    st.set_page_config(page_title="EDA CSV volumineux", layout="wide")
    st.title("EDA CSV volumineux")

    with st.sidebar:
        st.header("Fichier")
        uploaded = st.file_uploader("Ajouter un CSV dans data/raw", type=["csv"])
        if uploaded is not None:
            saved_path = save_uploaded_file(uploaded)
            st.success(f"Fichier ajoute: {saved_path.name}")

        csv_files = list_raw_csv_files()
        if not csv_files:
            st.info("Ajoutez un fichier CSV pour commencer.")
            return

        selected_file = st.selectbox(
            "CSV source",
            csv_files,
            index=choose_default_index(csv_files),
            format_func=lambda path: path.name,
        )
        encoding = st.text_input("Encodage", value="")
        sep = st.text_input("Separateur", value="")
        chunksize = st.number_input("Chunksize", min_value=1_000, max_value=1_000_000, value=100_000, step=10_000)

    encoding_value = encoding.strip() or None
    sep_value = sep.strip() or None

    try:
        resolved_encoding, resolved_sep = resolve_csv_options(selected_file, encoding_value, sep_value)
        sample = read_csv_sample(selected_file, encoding=resolved_encoding, sep=resolved_sep, nrows=1_000)
    except Exception as exc:
        st.error(f"Lecture impossible: {exc}")
        return

    st.subheader("Apercu")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Fichier", selected_file.name)
    metric_cols[1].metric("Colonnes", len(sample.columns))
    metric_cols[2].metric("Encodage", resolved_encoding)
    metric_cols[3].metric("Separateur", repr(resolved_sep))

    with st.expander("Details du fichier", expanded=False):
        try:
            st.write(
                {
                    "chemin": str(selected_file.relative_to(ROOT_DIR)),
                    "taille_octets": selected_file.stat().st_size,
                    "lignes_physiques": count_lines(selected_file),
                }
            )
        except Exception as exc:
            st.warning(f"Details incomplets: {exc}")

    st.dataframe(sample.head(100), use_container_width=True, height=320)

    st.subheader("Colonnes")
    column_stats = pd.DataFrame(
        {
            "column": sample.columns,
            "sample_non_null": [int(sample[column].notna().sum()) for column in sample.columns],
            "sample_unique": [int(sample[column].nunique(dropna=True)) for column in sample.columns],
            "sample_dtype": [str(dtype) for dtype in sample.dtypes],
        }
    )
    st.dataframe(column_stats, use_container_width=True, hide_index=True)

    st.subheader("Variantes textuelles")
    analyze_all_columns = st.checkbox("Analyser toutes les colonnes", value=True)
    text_only = st.checkbox("Limiter aux colonnes textuelles detectees", value=False, disabled=not analyze_all_columns)
    default_column = "recipient_legal_name" if "recipient_legal_name" in sample.columns else sample.columns[0]
    selected_column = st.selectbox(
        "Colonne a analyser",
        list(sample.columns),
        index=list(sample.columns).index(default_column),
        disabled=analyze_all_columns,
    )
    max_values = st.number_input("Valeurs distinctes maximum", min_value=100, max_value=100_000, value=20_000, step=1_000)

    if st.button("Generer le rapport de variantes", type="primary", use_container_width=True):
        try:
            variants = load_variants_module()
            if analyze_all_columns:
                target_columns = variants.resolve_target_columns(selected_file, None, resolved_encoding, resolved_sep, text_only)
                counts_by_column = variants.count_values_for_columns(
                    selected_file,
                    target_columns,
                    encoding=resolved_encoding,
                    sep=resolved_sep,
                    chunksize=int(chunksize),
                )
                report = variants.build_reports_for_columns(counts_by_column, int(max_values))
            else:
                counts = variants.count_values(
                    selected_file,
                    selected_column,
                    encoding=resolved_encoding,
                    sep=resolved_sep,
                    chunksize=int(chunksize),
                )
                report = variants.build_report(counts, int(max_values), column_name=selected_column)
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            report.to_csv(VARIANTS_REPORT, index=False)
            st.success(f"Rapport genere: {VARIANTS_REPORT.relative_to(ROOT_DIR)}")
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Generation impossible: {exc}")

    if VARIANTS_REPORT.exists():
        report_df = pd.read_csv(VARIANTS_REPORT)
        if analyze_all_columns:
            if "variant_view" not in st.session_state:
                st.session_state["variant_view"] = "suggested"

            view_cols = st.columns(3)
            if view_cols[0].button("Suggested", use_container_width=True):
                st.session_state["variant_view"] = "suggested"
            if view_cols[1].button("Original", use_container_width=True):
                st.session_state["variant_view"] = "original"
            if view_cols[2].button("Normalized", use_container_width=True):
                st.session_state["variant_view"] = "normalized"

            active_view = st.session_state["variant_view"]
            st.caption(f"Vue active: {active_view}")
            st.dataframe(
                csv_value_view(sample, report_df, active_view),
                use_container_width=True,
                height=420,
                hide_index=True,
            )
        else:
            st.dataframe(report_df, use_container_width=True, height=420, hide_index=True)
        render_report_download(VARIANTS_REPORT, "Telecharger organization_variants_report.csv")


if __name__ == "__main__":
    main()
