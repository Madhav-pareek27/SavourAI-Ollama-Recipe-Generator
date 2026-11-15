"""Pure helpers: ingredient normalization, validation and exports."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any


class RecipeInputError(ValueError):
    """Invalid user input that can safely be shown in the interface."""


def parse_ingredients(raw: str) -> list[str]:
    """Accept comma/newline/semicolon separated items without losing quantities."""
    if not isinstance(raw, str):
        raise RecipeInputError("Enter your available ingredients as text.")
    chunks = re.split(r"[,;\n]+", raw)
    result: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        ingredient = re.sub(r"\s+", " ", chunk.strip(" \t\r\u2022-"))
        if not ingredient:
            continue
        if len(ingredient) > 90:
            raise RecipeInputError("One ingredient is too long. Keep each item under 90 characters.")
        key = ingredient.casefold()
        if key not in seen:
            result.append(ingredient)
            seen.add(key)
    if not result:
        raise RecipeInputError("Add at least one ingredient before generating a recipe.")
    if len(result) > 25:
        raise RecipeInputError("Please use a maximum of 25 ingredients per recipe.")
    return result


def parse_avoid(raw: str) -> list[str]:
    return list(dict.fromkeys(x.strip() for x in re.split(r"[,;\n]+", raw or "") if x.strip()))[:20]


def list_of_strings(value: Any, limit: int = 20) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, (str, int, float)) and str(item).strip()][:limit]


def positive_number(value: Any, default: float = 0) -> float:
    try:
        value = float(value)
        if value < 0 or value > 20000:
            return default
        return round(value, 1)
    except (TypeError, ValueError):
        return default


def export_markdown(state: dict) -> str:
    recipe = state.get("recipe") or {}
    nutrition = state.get("nutrition") or {}
    tips = state.get("tips") or {}
    lines = [
        f"# {recipe.get('recipe_name', 'My AI Recipe')}",
        "",
        recipe.get("description", ""),
        "",
        f"**Cuisine:** {recipe.get('cuisine', state.get('cuisine', 'Any'))}  ",
        f"**Serves:** {recipe.get('servings', state.get('servings', 2))}  ",
        f"**Prep:** {recipe.get('prep_time_minutes', '—')} min  ",
        f"**Cook:** {recipe.get('cook_time_minutes', '—')} min",
        "",
        "## Ingredients",
    ]
    for item in recipe.get("ingredients", []):
        if isinstance(item, dict):
            lines.append(f"- {item.get('quantity', '')} {item.get('item', '')}".strip())
        else:
            lines.append(f"- {item}")
    lines += ["", "## Steps"]
    for i, step in enumerate(recipe.get("steps", []), 1):
        if isinstance(step, dict):
            lines.append(f"{i}. **{step.get('title', f'Step {i}')}** — {step.get('detail', '')}")
        else:
            lines.append(f"{i}. {step}")
    lines += ["", "## Estimated nutrition (per serving)"]
    for key, label in [
        ("calories_per_serving", "Calories (kcal)"),
        ("protein_g", "Protein (g)"), ("carbs_g", "Carbs (g)"),
        ("fat_g", "Fat (g)"), ("fiber_g", "Fiber (g)"),
    ]:
        lines.append(f"- {label}: {nutrition.get(key, '—')}")
    lines += ["", "_Nutrition values are rough AI estimates, not laboratory measurements._", "", "## Chef tips"]
    for tip in tips.get("chef_tips", []):
        lines.append(f"- {tip}")
    for key, label in [("serving_suggestion", "Serving idea"), ("storage_tip", "Storage"), ("food_safety_note", "Food safety")]:
        if tips.get(key):
            lines.append(f"- **{label}:** {tips[key]}")
    lines += ["", "---", f"Created with SavourAI on {datetime.now():%d %b %Y}."]
    return "\n".join(lines)


def as_json(state: dict) -> str:
    return json.dumps(state, ensure_ascii=False, indent=2)
