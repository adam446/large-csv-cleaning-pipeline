# Variantes de noms d'organisations

## Resume

- Fichier source: `data/raw/fichier_original.csv`
- Colonnes analysees: `id, recipient_legal_name, city, province, amount, category`
- Valeurs distinctes: `66`
- Rapport CSV: `reports/organization_variants_report.csv`
- Le fichier original n'est pas modifie.

## Apercu

| column_name | original_value | normalized_value | suggested_group | similarity_score | count | decision |
| --- | --- | --- | --- | --- | --- | --- |
| id | 7 | 7 | 1 | 0.0 | 1 | rejected |
| id | 8 | 8 | 1 | 0.0 | 1 | rejected |
| id | 9 | 9 | 1 | 0.0 | 1 | rejected |
| id | 10 | 10 | 1 | 90.0 | 1 | review |
| id | 11 | 11 | 1 | 90.0 | 1 | review |
| id | 12 | 12 | 1 | 90.0 | 1 | review |
| id | 13 | 13 | 1 | 90.0 | 1 | review |
| id | 14 | 14 | 1 | 90.0 | 1 | review |
| id | 15 | 15 | 1 | 90.0 | 1 | review |
| id | 16 | 16 | 1 | 90.0 | 1 | review |
| id | 1 | 1 | 10 | 90.0 | 1 | review |
| id | 2 | 2 | 12 | 90.0 | 1 | review |
| id | 3 | 3 | 13 | 90.0 | 1 | review |
| id | 4 | 4 | 14 | 90.0 | 1 | review |
| id | 5 | 5 | 15 | 90.0 | 1 | review |
| id | 6 | 6 | 16 | 90.0 | 1 | review |
| recipient_legal_name | Ministère de la Santé | MINISTERE DE LA SANTE | Ministère de la Santé | 100.0 | 1 | accepted |
| recipient_legal_name | Ministere de la Sante | MINISTERE DE LA SANTE | Ministère de la Santé | 100.0 | 1 | accepted |
| recipient_legal_name | MINISTERE SANTE | MINISTERE SANTE | Ministère de la Santé | 95.0 | 1 | accepted |
| recipient_legal_name | Société de transport de Montréal | SOCIETE DE TRANSPORT DE MONTREAL | Societe transport Montreal | 95.0 | 1 | accepted |
| recipient_legal_name | Societe transport Montreal | SOCIETE TRANSPORT MONTREAL | Société de transport de Montréal | 95.0 | 1 | accepted |
| recipient_legal_name | U.Q.A.M. | U Q A M | U.Q.A.M. | 100.0 | 1 | accepted |
| recipient_legal_name | U Q A M | U Q A M | U.Q.A.M. | 100.0 | 1 | accepted |
| recipient_legal_name | Université du Québec à Montréal | UNIVERSITE DU QUEBEC A MONTREAL | Université du Québec à Montréal | 100.0 | 1 | accepted |
| recipient_legal_name | Universite du Quebec a Montreal | UNIVERSITE DU QUEBEC A MONTREAL | Université du Québec à Montréal | 100.0 | 1 | accepted |
| recipient_legal_name | Ville de Montréal | VILLE DE MONTREAL | Ville de Montréal | 100.0 | 1 | accepted |
| recipient_legal_name | Ville de Montreal | VILLE DE MONTREAL | Ville de Montréal | 100.0 | 1 | accepted |
| recipient_legal_name | STM | STM | Ministère de la Santé | 60.0 | 1 | rejected |
| recipient_legal_name | Organisme sans lien | ORGANISME SANS LIEN | STM | 60.0 | 1 | rejected |
| recipient_legal_name | UQAM | UQAM | ?QAM | 85.71 | 1 | review |
| recipient_legal_name | AQAM | AQAM | ?QAM | 85.71 | 1 | review |
| recipient_legal_name | ?QAM | QAM | UQAM | 85.71 | 1 | review |
| city | Montreal | MONTREAL | Montreal | 100.0 | 7 | accepted |
| city | Montréal | MONTREAL | Montreal | 100.0 | 3 | accepted |
| city | Quebec | QUEBEC | Quebec | 100.0 | 2 | accepted |
| city | Québec | QUEBEC | Quebec | 100.0 | 1 | accepted |
| city | Laval | LAVAL | Montreal | 51.43 | 2 | rejected |
| city | Rimouski | RIMOUSKI | Montreal | 25.0 | 1 | rejected |
| province | QC | QC |  | 0.0 | 16 | rejected |
| amount | 120.00 | 120 00 | 100.00 | 83.33 | 1 | review |
| amount | 130.00 | 130 00 | 100.00 | 83.33 | 1 | review |
| amount | 140.00 | 140 00 | 100.00 | 83.33 | 1 | review |
| amount | 700.00 | 700 00 | 100.00 | 83.33 | 1 | review |
| amount | 800.00 | 800 00 | 100.00 | 83.33 | 1 | review |
| amount | 810.00 | 810 00 | 100.00 | 83.33 | 1 | review |
| amount | 100.00 | 100 00 | 120.00 | 83.33 | 1 | review |
| amount | 121.00 | 121 00 | 120.00 | 83.33 | 1 | review |
| amount | 500.00 | 500 00 | 50.00 | 90.91 | 1 | review |
| amount | 510.00 | 510 00 | 50.00 | 90.91 | 1 | review |
| amount | 50.00 | 50 00 | 500.00 | 90.91 | 1 | review |
