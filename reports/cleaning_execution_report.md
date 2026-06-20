# Rapport d'execution du nettoyage

## Resume

| total_lignes | lignes_sortie | corrections_appliquees | doublons_exacts_supprimes | colonnes_nettoyees | fichier_sortie |
| --- | --- | --- | --- | --- | --- |
| 53 | 50 | 110 | 3 | categorie_clean, date_clean, organisme_clean, province_clean, ville_clean | /home/adam4005/Bureau/big-file-eda-codex/data/processed/fichier_nettoye.csv |

## Regle appliquee

Seules les lignes du mapping avec `status = accepted` sont appliquees. Les statuts `review` et `rejected` restent inchanges.
