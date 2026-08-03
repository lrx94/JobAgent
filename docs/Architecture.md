# Architecture

## Vision

JobAgent est construit selon une architecture en couches.

Chaque couche possède une responsabilité unique.

Les dépendances sont dirigées vers le bas uniquement.

---

# Architecture générale

```text
                UI (Streamlit)
                      │
               Services / Use Cases
                      │
        ┌─────────────┴─────────────┐
        │                           │
 Candidate Engine             Job Engine
        │                           │
     CV Parsing               Job Parsing
        │                           │
        └─────────────┬─────────────┘
                      │
                  Domain Model
                      │
               Matching Engine
                      │
                 Repository
                      │
                    SQLite
```

---

# Structure du projet

```
src/

domain/
cv/
matching/
connectors/
knowledge/
services/
storage/
ui/
```

---

# Responsabilités

## domain/

Contient uniquement les objets métier.

Exemples :

* CV
* Experience
* Education
* Skill
* JobOffer
* MatchResult

Le domaine ne dépend d'aucune autre couche.

---

## cv/

Responsable du parsing des CV.

Exemples :

* PdfReader
* SectionParser
* ExperienceParser
* SkillParser
* CVBuilder

---

## connectors/

Responsable des connexions vers les sources externes.

Exemples futurs :

* France Travail
* APEC
* LinkedIn
* Indeed

---

## matching/

Responsable du calcul de compatibilité.

Composants prévus :

* MatchingEngine
* SkillMatcher
* ExperienceMatcher
* LanguageMatcher
* EducationMatcher
* Scorer

---

## knowledge/

Base de connaissances interne.

Contiendra notamment :

* référentiel de compétences
* synonymes
* taxonomie
* entreprises
* certifications

---

## storage/

Accès aux données.

Responsabilités :

* Repository
* SQLite

---

## ui/

Interface utilisateur.

Actuellement :

* Streamlit

---

# Conventions

Une classe = une responsabilité.

Un parser = une responsabilité.

Les Builders ne contiennent pas de logique métier.

Tous les parsers exposent :

```python
parse(text)
```

Les objets du domaine sont des dataclasses.

---

# Règles de dépendance

Une couche ne dépend que de la couche immédiatement inférieure.

Exemple :

```
UI
 ↓
Services
 ↓
Matching
 ↓
Domain
 ↓
Repository
 ↓
SQLite
```

Interdictions :

* Domain → Repository
* Domain → SQLite
* Parser → UI
* Matching → UI

---

# Dette technique connue

Le parser des centres d'intérêt utilise actuellement un hack spécifique au CV de test (`INTEREST_STOP`).

Ce comportement sera remplacé par un composant de normalisation de mise en page (Layout Analyzer).
