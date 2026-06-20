# EDA Report

## 1. Apercu general

- Chemin: `/home/adam4005/Bureau/big-file-eda-codex/data/raw/exemple_organismes.csv`
- Encodage: `utf-8`
- Separateur: `,`
- Taille: `3714` octets
- Nombre de lignes estime: `53`
- Nombre de colonnes: `8`

## 2. Colonnes

| column | sample_dtype | sample_non_null | sample_unique |
| --- | --- | --- | --- |
| id | string | 53 | 50 |
| date | string | 51 | 46 |
| organisme | string | 50 | 46 |
| ville | string | 53 | 14 |
| province | string | 53 | 2 |
| code_postal | string | 51 | 27 |
| montant | string | 50 | 39 |
| categorie | string | 52 | 23 |

## 3. Colonnes numeriques possibles

- id
- montant

## 4. Colonnes textuelles possibles

- date
- organisme
- ville
- province
- code_postal
- categorie

## 5. Colonnes de date possibles

- date

## 6. Apercu des premieres lignes

| id | date | organisme | ville | province | code_postal | montant | categorie |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2024-01-01 | UQAM | Montreal | QC | H2X 1Y4 | 100.00 | Education |
| 2 | 2024-01-02 | U.Q.A.M. | Montréal | QC | H2X 1Y4 | 200.50 | education |
| 3 | 2024-01-03 | Université du Québec à Montréal |  Montreal  | QC | H2X 1Y4 | 300.00 | Education |
| 4 | 2024-01-03 | Université du Québec à Montréal |  Montreal  | QC | H2X 1Y4 | 300.00 | Education |
| 5 | 2024-01-04 | AQAM | Laval | QC |  | 400.00 | Recherche |
| 6 | 2024-01-05 | ?QAM | Laval | QC | H7A 0A1 |  | Recherche |
| 7 | 2024-01-06 | universite du quebec a montreal | Quebec | QC | G1R 2B5 | 150.00 | EDUCATION |
| 8 |  |  Université  du Québec à Montréal  | Québec | QC | G1R 2B5 | 175.25 |  |
| 9 | 2024-01-08 | Ministere de la Sante | Montreal | QC | H1A 1A1 | 500.00 | Sante |
| 10 | 2024-01-09 | Ministère de la Santé |  Montréal | QC | H1A 1A1 | 510.00 | santé |
| 11 | 2024-01-10 | MINISTERE SANTE | Montreal | QC | H1A 1A1 | 490.00 | SANTE |
| 12 | 2024-01-11 | Ville de Montréal | Montréal | QC | H2Y 1C6 | 1000.00 | Municipal |
| 13 | 2024-01-12 | Ville de Montreal | Montreal | QC | H2Y 1C6 | 1000.00 | municipal |
| 14 | 2024-01-13 |  | Sherbrooke | QC | J1H 1A1 | 250.00 | Autre |
| 14 | 2024-01-13 |  | Sherbrooke | QC | J1H 1A1 | 250.00 | Autre |
| 15 | 2024-01-14 | U Q A M | Montreal | QC | H2X1Y4 | 125.00 | Education |
| 16 | 2024-01-15 | Univ. du Quebec a Montreal | Montréal | QC | H2X 1Y4 | 130.00 | Éducation |
| 17 | 2024-01-16 | Universite Québec Montreal | Montréal | QC | H2X 1Y4 | 131.00 | education  |
| 18 | 2024-01-17 | Université du Québec @ Montréal | Montréal | QC | H2X 1Y4 | 132.00 | EDUCATION |
| 19 | 2024-01-18 | Ministere de la Santé et Services Sociaux | Québec | QC | G1R 5M8 | 800.00 | Santé |
