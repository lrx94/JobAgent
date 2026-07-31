# Roadmap

## Vision

Construire un assistant intelligent capable :

1. d'analyser un candidat ;
2. d'analyser une offre d'emploi ;
3. de calculer un matching pertinent ;
4. d'expliquer ce matching ;
5. d'apprendre progressivement grâce à une base de connaissances.

---

# V2 — Stabilisation

✅ Parsing CV

* PDF Reader
* Section Parser
* Experience Parser
* Education Parser
* Language Parser
* Interest Parser
* Skill Parser
* CV Builder

---

# V3 — Candidate Engine

Objectif :

Construire un profil candidat robuste.

Sprints :

* Intégration SkillParser
* SkillNormalizer
* SkillClassifier
* Language Parser V2
* Interest Parser V2
* Experience Parser V2
* Education Parser V2

Livrable :

CandidateProfile complet.

---

# V4 — Job Engine

Objectif :

Analyser des offres réelles.

Connecteurs prévus :

* France Travail
* APEC
* LinkedIn
* Indeed

Livrable :

JobOffer.

---

# V5 — Matching Engine

Objectif :

Comparer un candidat à une offre.

Modules :

* MatchingEngine
* SkillMatcher
* ExperienceMatcher
* LanguageMatcher
* EducationMatcher
* Score global
* Explication du score

---

# V6 — Knowledge Engine

Objectif :

Construire une base de connaissances.

Fonctionnalités :

* référentiel compétences
* synonymes
* entreprises
* certifications
* enrichissement automatique

---

# V7 — AI Engine

Objectif :

Transformer JobAgent en véritable assistant intelligent.

Fonctions prévues :

* recommandations personnalisées
* optimisation des candidatures
* génération d'argumentaires
* apprentissage à partir des résultats
* enrichissement automatique de la Knowledge Base

---

# Règles de développement

Chaque sprint suit le cycle suivant :

1. Analyse
2. Conception
3. Développement
4. Tests unitaires
5. Tests d'intégration
6. Validation
7. Commit Git
8. Mise à jour de la documentation

Un composant validé est considéré comme gelé jusqu'à l'apparition d'un nouveau besoin fonctionnel ou d'un correctif de bug.

---

# Objectif MVP

Le premier MVP devra être capable de :

* parser un CV PDF ;
* parser des offres d'emploi ;
* calculer un score de matching ;
* expliquer ce score ;
* produire un rapport exploitable par un candidat.
