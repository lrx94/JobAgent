# Architecture

## Vue d'ensemble

JobAgent est organisé selon une architecture en couches.


┌─────────────────────┐
│      Streamlit      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│      Services       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│      Matching       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│     Repository      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│      SQLite         │
└─────────────────────┘


## Structure du projet
src/

domain/
job.py
profile.py
match_result.py

matching/
engine.py
scorer.py
skill_matcher.py
skill_dictionary.py

providers/
france_travail.py

services/
job_service.py

storage/
repository.py

ui/
dashboard.py
job_card.py


## Principes

- séparation UI / métier / stockage
- dataclasses pour les modèles
- repository unique
- matching indépendant des providers