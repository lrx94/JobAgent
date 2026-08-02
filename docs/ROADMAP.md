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


## V3.9.0 — Historisation et veille emploi ✅

- [x] Détection des nouvelles offres
- [x] Détection des mises à jour
- [x] Détection des offres inchangées
- [x] Compteur d'observations
- [x] Historique des dates
- [x] Requêtes analytiques du repository
- [x] Statistiques globales et par source

✔ V3.10
V3.11
Analyse métier

- Détection automatique du métier
- Détection de la séniorité
- Génération automatique de profils
- Référentiel métier
- Sélection intelligente des providers

## V3.12.2.2 — Domaine d'autorisation ✅

- [x] Contrat AuthorizationRepository
- [x] Repository de liste blanche
- [x] Normalisation des e-mails
- [x] AuthorizationService
- [x] AccessController
- [x] Contrôle des rôles
- [x] Tests unitaires sans Streamlit
- [x] Refus par défaut

## V3.12.2.3 — Adaptateur Google OIDC

- [ ] Conversion des claims Streamlit en CurrentUser
- [ ] Écran de connexion
- [ ] Déconnexion
- [ ] Protection de app.py
- [ ] Protection des pages
- [ ] Configuration locale secrets.toml
- [ ] Tests avec passerelle Streamlit simulée

## V3.12.2.4 — Déploiement privé Cloud ✅

- [x] Déploiement Streamlit Community Cloud
- [x] URL publique
- [x] Google OIDC Cloud
- [x] Secrets Cloud
- [x] Liste blanche
- [x] Connexion autorisée
- [x] Déconnexion
- [ ] Test avec un compte non autorisé

## V3.12.3.1 — Chemins utilisateurs sécurisés ✅

- [x] UserStoragePaths
- [x] Répertoire privé par user_id
- [x] Profils isolés par chemin
- [x] Bibliothèque CV préparée
- [x] Répertoire d'exports
- [x] Répertoire de cache
- [x] Base d'offres utilisateur préparée
- [x] Validation des identifiants
- [x] Protection contre les path traversals
- [x] Tests d'isolation

## V3.12.3.2 — Profils isolés

- [ ] Transmettre UserContext à CVProfileService
- [ ] Utiliser UserStoragePaths
- [ ] Lister uniquement les profils de l'utilisateur
- [ ] Créer les profils sous data/users/<user_id>
- [ ] Empêcher les lectures croisées
- [ ] Adapter la page CV et profils
- [ ] Tests avec deux utilisateurs

## V3.12.3.3-A — Repository multi-CV ✅

- [x] Modèle CVDocument
- [x] Repository isolé par utilisateur
- [x] Import de fichiers PDF
- [x] Métadonnées persistantes
- [x] Checksum SHA-256
- [x] Détection des doublons
- [x] Liste et chargement
- [x] Renommage
- [x] Suppression
- [x] Tests d'accès croisé

## V3.12.3.3-B — Service multi-CV

- [ ] CVService
- [ ] Limite de taille
- [ ] Politique de doublons
- [ ] Analyse du CV après import
- [ ] Enrichissement du titre
- [ ] Résultat d'import explicable
- [ ] Intégration avec CVParser