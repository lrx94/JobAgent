# Architecture du Career Workspace

## Version

V3.13.1 — Workspace Foundation

## Objectif

Le Career Workspace fournit une porte d'entrée unique vers les
services propres à un utilisateur JobAgent.

Les pages Streamlit ne doivent plus construire directement les
repositories ou services utilisateur.

## Point d'entrée

```python
workspace = build_workspace(
    user_context=user_context,
)