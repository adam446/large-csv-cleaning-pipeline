# Decisions de nettoyage

## Regles

- `accepted`: correction applicable automatiquement.
- `review`: correction probable mais non appliquee.
- `rejected`: correction refusee.

## Mapping

| column_name | original_value | clean_value | status | reason |
| --- | --- | --- | --- | --- |
| id | 7 | 7 | rejected | score de similarite 0.0 |
| id | 8 | 8 | rejected | score de similarite 0.0 |
| id | 9 | 9 | rejected | score de similarite 0.0 |
| id | 10 | 10 | review | score de similarite 90.0 |
| id | 11 | 11 | review | score de similarite 90.0 |
| id | 12 | 12 | review | score de similarite 90.0 |
| id | 13 | 13 | review | score de similarite 90.0 |
| id | 14 | 14 | review | score de similarite 90.0 |
| id | 15 | 15 | review | score de similarite 90.0 |
| id | 16 | 16 | review | score de similarite 90.0 |
| id | 1 | 1 | review | score de similarite 90.0 |
| id | 2 | 2 | review | score de similarite 90.0 |
| id | 3 | 3 | review | score de similarite 90.0 |
| id | 4 | 4 | review | score de similarite 90.0 |
| id | 5 | 5 | review | score de similarite 90.0 |
| id | 6 | 6 | review | score de similarite 90.0 |
| recipient_legal_name | Ministère de la Santé | Ministère de la Santé | accepted | score de similarite 100.0 |
| recipient_legal_name | Ministere de la Sante | Ministère de la Santé | accepted | score de similarite 100.0 |
| recipient_legal_name | MINISTERE SANTE | Ministère de la Santé | accepted | score de similarite 95.0 |
| recipient_legal_name | Société de transport de Montréal | Societe transport Montreal | accepted | score de similarite 95.0 |
| recipient_legal_name | Societe transport Montreal | Société de transport de Montréal | accepted | score de similarite 95.0 |
| recipient_legal_name | U.Q.A.M. | UQAM | accepted | variante evidente ou nom complet de l'UQAM |
| recipient_legal_name | U Q A M | UQAM | accepted | variante evidente ou nom complet de l'UQAM |
| recipient_legal_name | Université du Québec à Montréal | UQAM | accepted | variante evidente ou nom complet de l'UQAM |
| recipient_legal_name | Universite du Quebec a Montreal | UQAM | accepted | variante evidente ou nom complet de l'UQAM |
| recipient_legal_name | Ville de Montréal | Ville de Montréal | accepted | score de similarite 100.0 |
| recipient_legal_name | Ville de Montreal | Ville de Montréal | accepted | score de similarite 100.0 |
| recipient_legal_name | STM | STM | rejected | score de similarite 60.0 |
| recipient_legal_name | Organisme sans lien | Organisme sans lien | rejected | score de similarite 60.0 |
| recipient_legal_name | UQAM | UQAM | accepted | variante evidente ou nom complet de l'UQAM |
| recipient_legal_name | AQAM | AQAM | review | forte similarite avec UQAM mais validation requise |
| recipient_legal_name | ?QAM | ?QAM | review | forte similarite avec UQAM mais validation requise |
| city | Montreal | Montreal | accepted | score de similarite 100.0 |
| city | Montréal | Montreal | accepted | score de similarite 100.0 |
| city | Quebec | Quebec | accepted | score de similarite 100.0 |
| city | Québec | Quebec | accepted | score de similarite 100.0 |
| city | Laval | Laval | rejected | score de similarite 51.43 |
| city | Rimouski | Rimouski | rejected | score de similarite 25.0 |
| province | QC | QC | rejected | score de similarite 0.0 |
| amount | 120.00 | 120.00 | review | score de similarite 83.33 |
| amount | 130.00 | 130.00 | review | score de similarite 83.33 |
| amount | 140.00 | 140.00 | review | score de similarite 83.33 |
| amount | 700.00 | 700.00 | review | score de similarite 83.33 |
| amount | 800.00 | 800.00 | review | score de similarite 83.33 |
| amount | 810.00 | 810.00 | review | score de similarite 83.33 |
| amount | 100.00 | 100.00 | review | score de similarite 83.33 |
| amount | 121.00 | 121.00 | review | score de similarite 83.33 |
| amount | 500.00 | 500.00 | review | score de similarite 90.91 |
| amount | 510.00 | 510.00 | review | score de similarite 90.91 |
| amount | 50.00 | 50.00 | review | score de similarite 90.91 |
