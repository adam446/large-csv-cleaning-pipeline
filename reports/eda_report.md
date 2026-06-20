# EDA Report

## 1. Apercu general

- Chemin: `data/raw/fichier_original.csv`
- Encodage: `utf-8`
- Separateur: `,`
- Taille: `817` octets
- Nombre de lignes estime: `16`
- Nombre de colonnes: `6`

## 2. Colonnes

| column | sample_dtype | sample_non_null | sample_unique |
| --- | --- | --- | --- |
| id | string | 16 | 16 |
| recipient_legal_name | string | 16 | 16 |
| city | string | 16 | 6 |
| province | string | 16 | 1 |
| amount | string | 16 | 16 |
| category | string | 16 | 11 |

## 3. Colonnes numeriques possibles

- id
- amount

## 4. Colonnes textuelles possibles

- recipient_legal_name
- city
- province
- category

## 5. Colonnes de date possibles

_Aucune._

## 6. Apercu des premieres lignes

| id | recipient_legal_name | city | province | amount | category |
| --- | --- | --- | --- | --- | --- |
| 1 | UQAM | Montreal | QC | 100.00 | Education |
| 2 | U.Q.A.M. | Montréal | QC | 120.00 | Education |
| 3 | Université du Québec à Montréal | Montreal | QC | 130.00 | Education |
| 4 | Universite du Quebec a Montreal | Montreal | QC | 140.00 | education |
| 5 | AQAM | Laval | QC | 90.00 | Education |
| 6 | ?QAM | Laval | QC | 92.00 | Education |
| 7 | U Q A M | Montreal | QC | 121.00 | Education |
| 8 | Ministère de la Santé | Québec | QC | 500.00 | Sante |
| 9 | Ministere de la Sante | Quebec | QC | 510.00 | Santé |
| 10 | MINISTERE SANTE | Quebec | QC | 515.00 | SANTE |
| 11 | Ville de Montréal | Montréal | QC | 700.00 | Municipal |
| 12 | Ville de Montreal | Montreal | QC | 705.00 | municipal |
| 13 | Société de transport de Montréal | Montréal | QC | 800.00 | Transport |
| 14 | Societe transport Montreal | Montreal | QC | 805.00 | transport |
| 15 | STM | Montreal | QC | 810.00 | TRANSPORT |
| 16 | Organisme sans lien | Rimouski | QC | 50.00 | Autre |
