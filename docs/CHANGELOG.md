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

## [3.10.0] - 2026-08-01

### Added
- Premier provider réel RemoteOK.
- Architecture multi-providers.
- ProviderRegistry.
- JobAggregator.
- Workflow complet CV → RemoteOK.
- Extraction des compétences depuis un CV.
- Normalisation des compétences.
- Matching sémantique.
- Persistance des offres.

### Changed
- Les providers ne filtrent plus les compétences.
- Le matching devient responsable de la pertinence.
- Les offres sans compétence commune obtiennent désormais un score nul.

### Fixed
- Réduction des faux positifs.
- Normalisation des tags RemoteOK.
- Stabilisation de JobService.

## [3.12.2.2] - 2026-08-02

### Added

- Contrat générique `AuthorizationRepository`.
- Repository JSON de liste blanche.
- Normalisation et validation des adresses e-mail.
- Mise en cache et rechargement de la liste blanche.
- Service d'autorisation indépendant du stockage.
- Contrôleur d'accès produisant un `UserContext`.
- Contrôle des rôles applicatifs.
- Refus par défaut des comptes absents de la liste blanche.

## [3.12.2.4] - 2026-08-02

### Added

- Déploiement privé de JobAgent sur Streamlit Community Cloud.
- Configuration Google OIDC de production.
- URI OAuth de production.
- Secrets sécurisés dans Streamlit Cloud.
- Authentification Google validée sur l'URL publique.
- Accès limité aux comptes présents dans la liste blanche.