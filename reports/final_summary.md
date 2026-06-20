# Rapport final

## Indicateurs

| indicateur | valeur |
| --- | --- |
| lignes_fichier_original | 16 |
| colonnes_fichier_original | 6 |
| doublons_detectes | 0 |
| organismes_uniques_avant | 16 |
| organismes_uniques_apres | 9 |
| corrections_acceptees | 26 |
| corrections_a_verifier | 31 |

## Valeurs manquantes par colonne

| colonne | valeurs_manquantes |
| --- | --- |
| id | 0 |
| recipient_legal_name | 0 |
| city | 0 |
| province | 0 |
| amount | 0 |
| category | 0 |

## Limites du nettoyage

- Les scores fuzzy ne prouvent pas qu'il s'agit de la meme entite.
- Les statuts `review` ne sont pas appliques automatiquement.
- Les corrections doivent etre confirmees avec le contexte metier: adresse, ville, province, code postal, numero d'entreprise.

## Recommandations

- Valider manuellement les lignes `review` du mapping.
- Ajouter des identifiants officiels d'organismes si disponibles.
- Conserver la colonne originale et auditer regulierement le rapport de nettoyage.
