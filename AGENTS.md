# AGENTS

## Role du projet

Ce projet sert d'exercice pratique pour l'EDA, la qualite des donnees et le nettoyage prudent d'un fichier CSV volumineux.

## Regles de travail

- Ne jamais modifier `data/raw/fichier_original.csv`.
- Utiliser `pandas.read_csv(..., chunksize=...)` pour les scripts qui parcourent tout le fichier.
- Produire des rapports dans `reports/` avant d'appliquer des corrections.
- Appliquer seulement les mappings avec `status = accepted`.
- Garder les valeurs `review` et `rejected` inchangees dans le fichier nettoye.
- Conserver la colonne originale et ajouter une colonne propre suffixee par `_clean`.

## Commandes principales

```bash
python src/01_inspect_file.py
python src/02_missing_values.py
python src/03_detect_duplicates.py
python src/04_detect_text_variants.py
python src/05_build_cleaning_mapping.py
python src/06_clean_file.py
python src/07_final_summary.py
```
