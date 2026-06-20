# Big File EDA and Cleaning with Codex

## 1. Objectif

Ce projet analyse et nettoie un fichier CSV volumineux contenant des donnees administratives: organismes, beneficiaires, villes, provinces, montants, dates et colonnes textuelles.

La methode suit une logique professionnelle:

```text
Detecter -> proposer -> valider -> corriger -> documenter
```

## 2. Problemes traites

- valeurs manquantes;
- doublons exacts et doublons probables;
- accents, caracteres speciaux, espaces multiples et casse incoherente;
- variantes d'organismes comme `UQAM`, `U.Q.A.M.`, `AQAM`, `?QAM`;
- nettoyage traçable sans ecraser la colonne originale.

## 3. Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Placez le fichier brut dans:

```text
data/raw/fichier_original.csv
```

## 4. Execution

```bash
python src/01_inspect_file.py
python src/02_missing_values.py
python src/03_detect_duplicates.py
python src/04_detect_text_variants.py
python src/05_build_cleaning_mapping.py
python src/06_clean_file.py
python src/07_final_summary.py
```

Par defaut, `04_detect_text_variants.py` analyse toutes les colonnes du CSV et ajoute `column_name` au rapport.

Pour cibler uniquement une colonne:

```bash
python src/04_detect_text_variants.py --org-column organisme
python src/06_clean_file.py --org-column organisme
python src/07_final_summary.py --org-column organisme
```

Pour limiter l'analyse automatique aux colonnes detectees comme textuelles:

```bash
python src/04_detect_text_variants.py --text-only
```

## 5. Resultats

Les fichiers principaux sont generes dans `reports/`:

- `eda_report.md`
- `missing_values_report.csv`
- `duplicates_report.csv`
- `organization_variants_report.csv`
- `entity_cleaning_mapping.csv`
- `cleaning_execution_report.md`
- `final_summary.md`

Le fichier nettoye est produit ici:

```text
data/processed/fichier_nettoye.csv
```

## 6. Interface Streamlit

```bash
python -m streamlit run streamlit_app.py
```

Dans cet environnement, l'installation a manque d'espace pour creer `.venv/bin/streamlit`, mais le lancement via module fonctionne si Streamlit est installe:

```bash
.venv/bin/python -m streamlit run streamlit_app.py
```

## 7. Limites

Les corrections automatiques doivent etre validees avant usage en production. Un score fuzzy eleve ne prouve pas qu'il s'agit de la meme entite; il faut verifier le contexte metier comme l'adresse, la ville, la province, le code postal ou un identifiant officiel.

## 8. Questions d'analyse

1. Pourquoi ne faut-il pas corriger automatiquement toutes les valeurs similaires ?
   Parce qu'une similarite textuelle peut rapprocher deux organisations differentes. Une correction automatique non validee peut creer de fausses donnees.

2. Pourquoi `AQAM` ne doit-il pas etre automatiquement transforme en `UQAM` sans validation ?
   `AQAM` peut etre une faute de frappe, mais peut aussi designer une autre entite. Le contexte doit confirmer la correction.

3. Pourquoi faut-il garder la colonne originale et creer une nouvelle colonne nettoyee ?
   Pour conserver la traçabilite, permettre l'audit et revenir en arriere si une correction est contestee.

4. Quelle est la difference entre une correction `accepted` et une correction `review` ?
   `accepted` est appliquee automatiquement. `review` est une suggestion a verifier et n'est pas appliquee.

5. Pourquoi les valeurs manquantes peuvent-elles parfois contenir une information importante ?
   Une absence peut signaler un cas metier particulier, une saisie incomplete, une non-applicabilite ou une source de donnees differente.

6. Pourquoi un fichier volumineux doit-il etre traite avec `chunksize` ou un outil adapte ?
   Pour eviter de charger tout le fichier en memoire et rendre le traitement stable sur des machines limitees.

7. Pourquoi un rapport de nettoyage est-il important dans un projet professionnel ?
   Il documente les decisions, justifie les transformations et rend le nettoyage reproductible.

8. Quelle est la difference entre une erreur de saisie, une variante normale et une vraie organisation differente ?
   Une erreur de saisie est accidentelle, une variante normale est une autre ecriture valide, et une organisation differente represente une entite distincte qu'il ne faut pas fusionner.
