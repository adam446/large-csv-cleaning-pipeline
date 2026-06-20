# Rapport d'execution du nettoyage

## Resume

| total_lignes | corrections_appliquees | colonnes_nettoyees | fichier_sortie |
| --- | --- | --- | --- |
| 16 | 19 | category_clean, city_clean, recipient_legal_name_clean | data/processed/fichier_nettoye.csv |

## Regle appliquee

Seules les lignes du mapping avec `status = accepted` sont appliquees. Les statuts `review` et `rejected` restent inchanges.
