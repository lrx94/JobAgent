from __future__ import annotations

import ast
from pathlib import Path


PAGE_PATH = Path("pages/01_Career_Workspace.py")


def _function(name: str) -> ast.FunctionDef:
    tree = ast.parse(PAGE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Fonction UI absente : {name}")


def _tab_labels(function_name: str) -> list[list[str]]:
    labels: list[list[str]] = []
    for node in ast.walk(_function(function_name)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "tabs":
            continue
        if not node.args or not isinstance(node.args[0], ast.List):
            continue
        labels.append(
            [
                item.value
                for item in node.args[0].elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
        )
    return labels


def test_workspace_uses_four_primary_tabs() -> None:
    assert _tab_labels("render_workspace_dashboard") == [[
        "Profil",
        "Market Insights",
        "Learning",
        "Recherche & Offres",
    ]]


def test_profile_no_longer_contains_offers_subtab() -> None:
    assert _tab_labels("render_profile_dashboard") == [[
        "Vue d’ensemble",
        "Compétences",
        "CV associés",
        "Bibliothèque",
    ]]


def test_search_is_only_started_by_the_search_button() -> None:
    function = _function("render_search_panel")
    search_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_profile_search"
    ]
    assert len(search_calls) == 1
    assert any(
        isinstance(node, ast.If)
        and search_calls[0] in tuple(ast.walk(node))
        for node in ast.walk(function)
    )


def test_selected_profile_automatically_ensures_search_data() -> None:
    source = PAGE_PATH.read_text(encoding="utf-8")
    assert "search_availability = ensure_profile_search(" in source
    assert "profile_id=selected_profile.profile_id" in source


def test_page_has_no_permanent_dashboard_search_columns() -> None:
    source = PAGE_PATH.read_text(encoding="utf-8")
    assert "dashboard_column, search_column" not in source
    assert "workspace_search_scroll" not in source
