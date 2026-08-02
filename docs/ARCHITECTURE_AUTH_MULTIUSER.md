# JobAgent — Architecture d’authentification et d’isolation utilisateur

## 1. Objet du document

Ce document définit l’architecture cible de JobAgent pour :

- protéger une application exposée sur une URL publique ;
- imposer une authentification avant tout accès ;
- limiter initialement l’accès à une liste blanche ;
- isoler les profils, CV, recherches et offres par utilisateur ;
- préparer le passage de SQLite à PostgreSQL ;
- préparer le stockage sécurisé des CV hors du disque local ;
- éviter toute fuite de données entre utilisateurs.

Cette architecture doit rester indépendante de Streamlit dans les couches métier.

---

## 2. Contexte actuel

JobAgent stocke actuellement les profils dans un répertoire global :

```text
profiles/
├── data_engineer/
├── dsi_cio/
├── cloud_architect/
└── ...