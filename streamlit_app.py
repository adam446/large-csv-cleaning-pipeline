from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
RAW_DIR = ROOT_DIR / "data" / "raw"
REPORTS_DIR = ROOT_DIR / "reports"
VARIANTS_REPORT = REPORTS_DIR / "organization_variants_report.csv"
EDA_REPORT = REPORTS_DIR / "eda_report.md"
MISSING_REPORT = REPORTS_DIR / "missing_values_report.csv"
DUPLICATES_REPORT = REPORTS_DIR / "duplicates_report.csv"
MAPPING_REPORT = REPORTS_DIR / "entity_cleaning_mapping.csv"
CLEANED_FILE = ROOT_DIR / "data" / "processed" / "fichier_nettoye.csv"

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


def run_script(script_name: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SRC_DIR / script_name), *args]
    return subprocess.run(command, cwd=ROOT_DIR, text=True, capture_output=True, check=False)


def common_script_args(
    selected_file: Path,
    encoding_override: str | None,
    sep_override: str | None,
    chunksize: int,
) -> list[str]:
    args = [
        "--input",
        str(selected_file),
        "--chunksize",
        str(chunksize),
        "--reports-dir",
        str(REPORTS_DIR),
    ]
    if encoding_override:
        args.extend(["--encoding", encoding_override])
    if sep_override:
        args.extend(["--sep", sep_override])
    return args


def show_run_result(result: subprocess.CompletedProcess[str], success_message: str) -> None:
    if result.returncode == 0:
        st.success(success_message)
        if result.stdout.strip():
            st.code(result.stdout.strip())
        return
    st.error("Analyse echouee.")
    st.code((result.stderr or result.stdout or "Erreur inconnue").strip())


def render_csv_report(path: Path, title: str) -> None:
    if not path.exists():
        return
    with st.expander(title, expanded=False):
        df = pd.read_csv(path)
        st.dataframe(df, use_container_width=True, hide_index=True)
        render_report_download(path, f"Telecharger {path.name}")


def render_markdown_report(path: Path, title: str) -> None:
    if not path.exists():
        return
    with st.expander(title, expanded=False):
        st.markdown(path.read_text(encoding="utf-8"))


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


def corrections_table(sample: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    required = {"original_value", "clean_value", "status"}
    if not required.issubset(mapping_df.columns):
        return pd.DataFrame()

    accepted = mapping_df[mapping_df["status"].astype("string").str.lower() == "accepted"]
    rows = []
    row_number_label = "row_number"
    for column in sample.columns:
        values = sample[column].dropna().astype("string").str.strip()
        if not values.empty and pd.to_numeric(values, errors="coerce").notna().mean() >= 0.8:
            continue

        if "column_name" in accepted.columns:
            column_mapping = accepted[accepted["column_name"].astype("string") == column]
        else:
            column_mapping = accepted
        if column_mapping.empty:
            continue

        lookup = {
            cell_key(row.original_value): {
                "clean_value": cell_key(row.clean_value),
                "status": getattr(row, "status", ""),
                "reason": getattr(row, "reason", ""),
            }
            for row in column_mapping.itertuples(index=False)
        }

        for index, value in sample[column].items():
            original_value = cell_key(value)
            correction = lookup.get(original_value)
            if not correction:
                continue
            clean_value = correction["clean_value"]
            if clean_value == "" or clean_value == original_value:
                continue
            rows.append(
                {
                    row_number_label: index + 1,
                    "column_name": column,
                    "original_value": original_value,
                    "clean_value": clean_value,
                    "status": correction["status"],
                    "reason": correction["reason"],
                }
            )

    return pd.DataFrame(
        rows,
        columns=[row_number_label, "column_name", "original_value", "clean_value", "status", "reason"],
    )


def main() -> None:
    st.set_page_config(page_title="EDA CSV volumineux", layout="wide")
    st.title("Nettoyage CSV")

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

        with st.expander("Options avancees", expanded=False):
            encoding = st.text_input("Encodage", value="")
            sep = st.text_input("Separateur", value="")
            chunksize = st.number_input("Chunksize", min_value=1_000, max_value=1_000_000, value=100_000, step=10_000)

        st.header("Variantes")
        analyze_all_columns = st.checkbox("Toutes les colonnes", value=True)
        text_only = st.checkbox("Colonnes textuelles seulement", value=False, disabled=not analyze_all_columns)

    encoding_value = encoding.strip() or None
    sep_value = sep.strip() or None

    try:
        resolved_encoding, resolved_sep = resolve_csv_options(selected_file, encoding_value, sep_value)
        sample = read_csv_sample(selected_file, encoding=resolved_encoding, sep=resolved_sep, nrows=1_000)
    except Exception as exc:
        st.error(f"Lecture impossible: {exc}")
        return

    metric_cols = st.columns(4)
    metric_cols[0].metric("Fichier", selected_file.name)
    metric_cols[1].metric("Colonnes", len(sample.columns))
    metric_cols[2].metric("Encodage", resolved_encoding)
    metric_cols[3].metric("Separateur", repr(resolved_sep))

    action_args = common_script_args(selected_file, encoding_value, sep_value, int(chunksize))
    action_cols = st.columns(4)

    if action_cols[0].button("Analyser", type="primary", use_container_width=True):
        scripts = [("01_inspect_file.py", "Inspection"), ("02_missing_values.py", "Valeurs manquantes"), ("03_detect_duplicates.py", "Doublons")]
        failed = False
        for script_name, label in scripts:
            result = run_script(script_name, action_args)
            if result.returncode != 0:
                failed = True
                st.error(f"{label}: echec")
                st.code((result.stderr or result.stdout).strip())
                break
        if not failed:
            st.success("Analyse terminee.")

    default_column = "recipient_legal_name" if "recipient_legal_name" in sample.columns else sample.columns[0]
    selected_column = default_column
    max_values = 20_000

    if not analyze_all_columns:
        selected_column = st.selectbox("Colonne a analyser", list(sample.columns), index=list(sample.columns).index(default_column))

    if action_cols[1].button("Variantes", use_container_width=True):
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
            st.success("Variantes generees.")
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Generation impossible: {exc}")

    if action_cols[2].button("Mapping", use_container_width=True):
        result = run_script("05_build_cleaning_mapping.py", ["--reports-dir", str(REPORTS_DIR)])
        show_run_result(result, "Mapping genere.")

    if action_cols[3].button("Nettoyer + dedoublonner", use_container_width=True):
        clean_args = [*action_args, "--mapping", str(MAPPING_REPORT), "--output", str(CLEANED_FILE)]
        result = run_script("06_clean_file.py", clean_args)
        show_run_result(result, "Fichier nettoye genere.")

    preview_tab, quality_tab, variants_tab, corrections_tab, reports_tab = st.tabs(
        ["Apercu", "Qualite", "Variantes", "Corrections", "Rapports"]
    )

    with preview_tab:
        st.dataframe(sample.head(100), use_container_width=True, height=360)
        with st.expander("Colonnes"):
            column_stats = pd.DataFrame(
                {
                    "column": sample.columns,
                    "sample_non_null": [int(sample[column].notna().sum()) for column in sample.columns],
                    "sample_unique": [int(sample[column].nunique(dropna=True)) for column in sample.columns],
                    "sample_dtype": [str(dtype) for dtype in sample.dtypes],
                }
            )
            st.dataframe(column_stats, use_container_width=True, hide_index=True)
        with st.expander("Details du fichier"):
            st.write(
                {
                    "chemin": str(selected_file.relative_to(ROOT_DIR)),
                    "taille_octets": selected_file.stat().st_size,
                    "lignes_physiques": count_lines(selected_file),
                }
            )

    with quality_tab:
        render_csv_report(MISSING_REPORT, "Valeurs manquantes")
        render_csv_report(DUPLICATES_REPORT, "Doublons")

    with variants_tab:
        if not VARIANTS_REPORT.exists():
            st.info("Cliquez sur Variantes pour generer le rapport.")
        else:
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
                st.dataframe(csv_value_view(sample, report_df, st.session_state["variant_view"]), use_container_width=True, height=420, hide_index=True)
            else:
                st.dataframe(report_df, use_container_width=True, height=420, hide_index=True)
            render_report_download(VARIANTS_REPORT, "Telecharger organization_variants_report.csv")

    with corrections_tab:
        if MAPPING_REPORT.exists():
            mapping_df = pd.read_csv(MAPPING_REPORT)
            corrections = corrections_table(sample, mapping_df)
            if corrections.empty:
                st.info("Aucune correction accepted ne modifie les lignes visibles dans l'apercu.")
            else:
                st.metric("Corrections visibles", len(corrections))
                st.dataframe(corrections, use_container_width=True, height=360, hide_index=True)
            render_report_download(MAPPING_REPORT, "Telecharger entity_cleaning_mapping.csv")
        else:
            st.info("Cliquez sur Mapping apres avoir genere les variantes.")
        if CLEANED_FILE.exists():
            st.dataframe(pd.read_csv(CLEANED_FILE, nrows=100), use_container_width=True, height=300)
            render_report_download(CLEANED_FILE, "Telecharger fichier_nettoye.csv")

    with reports_tab:
        render_markdown_report(EDA_REPORT, "EDA")
        render_markdown_report(REPORTS_DIR / "cleaning_execution_report.md", "Execution du nettoyage")
        render_markdown_report(REPORTS_DIR / "final_summary.md", "Resume final")


if __name__ == "__main__":
    main()
