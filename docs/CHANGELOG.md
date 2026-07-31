# Changelog

## v1.1.0-beta

### Added

- Matching Engine
- Multi profils
- Dashboard Streamlit
- SQLite
- GitHub

### In Progress

- Repository V2
- Historique
- Favoris
## Sprint B3.2

### Architecture
- Migration complète de `src.models` vers `src.domain`
- Suppression du conflit `models.py` / `models/`

### Storage
- Repository V2
- CRUD complet
- Retour des objets `Job` au lieu des `sqlite3.Row`

### Qualité
- Architecture plus modulaire
- Préparation des fonctionnalités Favoris / Historique / Candidatures

## [3.9.0] - 2026-07-31

### Added

- Détection des nouvelles offres.
- Détection des offres modifiées.
- Détection des offres inchangées.
- Métadonnées first_seen_at, last_seen_at et updated_at.
- Compteur seen_count.
- Empreinte SHA-256 du contenu des offres.
- Requêtes pour les offres nouvelles, récentes et les meilleurs scores.
- Statistiques globales et statistiques par source.
- Résultats détaillés de sauvegarde dans JobService.

### Changed

- JobRepository.save retourne désormais RepositorySaveResult.
- Migration SQLite automatique vers le schéma V3.9.
- Suppression de la double sauvegarde éventuelle dans app.py.