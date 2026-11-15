"""SavourAI — attractive, local Streamlit front-end for the 5-node LangGraph agent."""
from __future__ import annotations

import html
from functools import partial
import os
from pathlib import Path

import streamlit as st

from ollama_client import RecipeAIError, ask_ollama_json, model_name, list_local_models, check_ollama_connection
from storage import delete_recipe, get_recipe, list_recipes, save_recipe, set_favorite
from utils import RecipeInputError, export_markdown, positive_number

st.set_page_config(
    page_title="SavourAI · Your AI Recipe Studio",
    page_icon="🍋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "SavourAI — 5-node LangGraph + local Ollama recipe generation."},
)

PHOTO = "https://images.unsplash.com/photo-1680359869958-fbdf77a5cbc0?auto=format&fit=crop&w=1200&q=85"

def h(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


STYLES = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&display=swap');
:root {--cream:#faf8f3; --forest:#1f3c31; --lime:#d9e8ba; --orange:#ea7544; --ink:#24392d; --muted:#748173; --line:#e9e8df;}
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family:'DM Sans', 'Segoe UI', sans-serif;}
.stApp {background: radial-gradient(circle at 100% 0%, #fff3dd 0%, transparent 34%), #faf8f3; color: #24392d;}
[data-testid="stMainBlockContainer"], .main .block-container {max-width: 1440px; padding: 1.75rem 2.5rem 5rem;}
[data-testid="stSidebar"] {background:#fffdf9; border-right:1px solid #ede8df;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap: 1.0rem;}
[data-testid="stSidebar"] .block-container {padding-top: 1.6rem;}
[data-testid="stSidebar"] label {font-weight: 700 !important;color: #334e3c !important;}
h1,h2,h3,h4 {color:#273f31; letter-spacing:-.025em;}
[data-testid="stMarkdownContainer"] p {line-height: 1.65;}
[data-testid="stForm"] {border:1px solid #e6e8dd; padding:1.45rem; border-radius:20px; background:#fffefb; box-shadow:0 14px 35px rgba(38,64,41,.035);}
[data-testid="stTextArea"] textarea {background:#fffefa; border:1.5px solid #e4e7dd; border-radius:13px; color:#24392d; font-size:1.04rem; line-height:1.7; padding:14px;}
[data-testid="stTextInput"] input, [data-baseweb="select"]>div {border-radius:11px; background: #ffffff;}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {border:none !important;border-radius:13px !important;background:#e97647 !important;color:white !important;min-height:50px;font-weight:800 !important;box-shadow:0 8px 20px rgba(227,105,64,.16);}
.stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {background:#d86033 !important;}
.stButton button[kind="secondary"] {border:1px solid #e2e6da !important; background:#fffdf9 !important; color:#41624c !important; border-radius:12px !important; font-weight:650;}
.stButton button[kind="secondary"]:hover {border-color:#c4d0b9 !important; background:#f5f8ef !important;}
[data-testid="stDownloadButton"] button {border-radius:12px;border:1px solid #cddacc;background:#f1f5e9;color:#345640;font-weight:700;}
.stTabs [data-baseweb="tab-list"] {gap:18px; border-bottom:1px solid #e8eadf; background:transparent;}
.stTabs [data-baseweb="tab"] {font-size: .95rem; color:#758675; padding:13px 12px; font-weight:700;}
.stTabs [aria-selected="true"] {color:#294c35 !important;}
.stTabs [data-baseweb="tab-highlight"] {background-color:#e97647; height:3px;border-radius:6px;}
.stTabs [data-baseweb="tab-border"] {display:none;}
[data-testid="stAlert"] {border-radius:14px;}
[data-testid="stMetric"] {background:white;border:1px solid #e8e9df;border-radius:16px;padding:16px;}
footer {visibility:hidden;}
.hero {display:flex;align-items:center;justify-content:space-between;min-height:286px;padding:38px 45px;border-radius:26px;overflow:hidden;position:relative; margin-bottom:26px;
  background:linear-gradient(95deg,#244934 0%,#244934 45%,rgba(36,73,52,.87) 61%,rgba(36,73,52,.33) 100%),
  url('https://images.unsplash.com/photo-1680359869958-fbdf77a5cbc0?auto=format&fit=crop&w=1600&q=85') center right/cover;
  box-shadow:0 20px 44px rgba(31,65,39,.12);}
.hero:before {content:'✳';font-size:140px;color:#a4c9910e;position:absolute;right:34%;top:-42px;}
.hero-copy {position:relative;z-index:2;max-width:730px;}
.hero-eyebrow {display:inline-block;background:#ffffff1c;color:#d5efc6;padding:8px 14px;border:1px solid #ffffff26;border-radius:100px;font-size:11px;font-weight:800;letter-spacing:2.2px;text-transform:uppercase;}
.hero h1 {font-family:'Playfair Display', Georgia, serif;font-size:clamp(32px,3.4vw,53px);line-height:1.16;letter-spacing:-1.2px;color:#fffaf1;margin:20px 0 14px;}
.hero h1 em {color:#f3cf9f;}
.hero p {color:#dcebdc;font-size:15px;margin:0;max-width:490px;line-height:1.65;}
.hero-chips {display:flex;gap:9px;flex-wrap:wrap;margin-top:24px;}
.hero-chip {color:#fff4df;border:1px solid #ffffff35;padding:7px 11px;border-radius:100px;font-size:12px;background:#ffffff10;font-weight:600;}
.brand-logo {display:flex; align-items:center;gap:12px;margin:4px 0 1px;}
.brand-mark {height:47px;width:47px;background:#e97745;border-radius:16px;display:grid;place-items:center;font-size:25px;box-shadow:0 9px 19px #e9774530;}
.brand-name {font-weight:900;font-size:27px;letter-spacing:-1.4px;color:#244735;line-height:1;}
.brand-sub {font-size:11px;color:#8b9889;letter-spacing:1.8px;text-transform:uppercase;margin-top:5px;font-weight:800;}
.side-pill {padding:12px 15px;border-radius:13px;font-size:13px;font-weight:700;line-height:1.45;margin:8px 0 15px;}
.side-ok {background:#edf6e9;color:#376c42;border:1px solid #dbe8d3;}
.side-miss {background:#fff4e9;color:#9a6030;border:1px solid #f4dfc9;}
.side-heading {font-weight:800;font-size:12px;letter-spacing:1.8px;text-transform:uppercase;color:#9d9f87;margin:8px 0 12px;}
.side-tip {background:#f3f5ec;border:1px solid #e4e8d9;border-radius:17px;padding:16px;color:#536d52;font-size:12px;line-height:1.75;margin:12px 0;}
.side-tip strong {display:block;color:#284c36;font-size:14px;margin-bottom:6px;}
.section-kicker {font-size:11px;font-weight:900;color:#dc774a;letter-spacing:2.3px;text-transform:uppercase;margin-bottom:7px;}
.section-title {font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:29px;color:#2a4432;margin:0 0 8px;letter-spacing:-.5px;}
.section-desc {color:#7d8b7a;font-size:14px;line-height:1.6;margin-bottom:16px;}
.inspo {border:1px solid #e3e9dc;background:white;border-radius:24px;overflow:hidden;box-shadow:0 10px 30px #2d42230a;}
.inspo-img {position:relative;height:224px;background:#efc69f url('https://images.unsplash.com/photo-1680359869958-fbdf77a5cbc0?auto=format&fit=crop&w=900&q=85') center center/cover;}
.inspo-tag {position:absolute;top:18px;left:18px;padding:8px 12px;border-radius:100px;background:#fffdf2;color:#436441;font-weight:900;letter-spacing:1px;font-size:10px;box-shadow:0 4px 10px #00000015;}
.inspo-copy {padding:21px 25px 24px;}
.inspo-kicker {color:#e97949;font-weight:900;letter-spacing:1.6px;font-size:10px;text-transform:uppercase;}
.inspo h3 {font-family:'Playfair Display',Georgia,serif;font-size:27px;margin:7px 0 9px;color:#244130;}
.inspo p {font-size:13px;color:#81907b;line-height:1.65;margin:0 0 13px;}
.inspo-badges {display:flex;gap:8px;flex-wrap:wrap;}
.inspo-badge {background:#f3f5eb;border-radius:9px;padding:7px 10px;color:#567151;font-weight:750;font-size:11px;}
.quick-help {font-size:12px;color:#8a9785;margin-bottom:8px;}
.result-banner {background:linear-gradient(108deg,#ecf3e3,#fffaf3);border:1px solid #e2e9d9;border-radius:21px;padding:23px 27px;margin:20px 0 17px;}
.result-eyebrow {font-weight:900;color:#e07744;letter-spacing:2.0px;text-transform:uppercase;font-size:11px;}
.result-banner h2 {font-family:'Playfair Display',Georgia,serif;font-size:clamp(29px,2.8vw,41px);margin:5px 0 5px;color:#284333;}
.result-banner p {color:#72816e;margin:0;font-size:14px;line-height:1.65;}
.stat-tile {background:white;border:1px solid #e8eadf;border-radius:17px;padding:16px 17px;margin-bottom:15px;min-height:90px;}
.stat-tile .stat-label {text-transform:uppercase;color:#899487;font-size:10px;font-weight:900;letter-spacing:1.2px;}
.stat-tile .stat-value {color:#2f4b36;font-size:23px;letter-spacing:-.5px;font-weight:900;margin-top:8px;}
.content-card {background:#fffefa;border:1px solid #e8e9df;border-radius:20px;padding:23px 24px;margin-bottom:18px;box-shadow:0 8px 25px #26402d06;}
.content-card h3 {font-family:'Playfair Display', Georgia,serif;font-size:23px;color:#2b4635;margin:0 0 17px;}
.ing-row {padding:10px 0;border-bottom:1px solid #efefe9;display:flex;gap:10px;align-items:flex-start;font-size:14px;color:#536451;}
.ing-row:last-child {border:none;}
.ing-dot {height:10px;width:10px;border:2px solid #e58d5f;border-radius:50%;margin-top:6px;flex:none;}
.ing-missing {color:#ba6b43;font-size:10px;font-weight:800;margin-left:auto;white-space:nowrap;}
.step-row {display:flex;align-items:flex-start;gap:16px;margin:4px 0 20px;}
.step-number {flex:none;height:37px;width:37px;display:grid;place-items:center;background:#ecf2e1;color:#3b6846;border-radius:13px;font-weight:900;}
.step-main {flex:1;}
.step-main strong {font-size:15px;color:#304d39;}
.step-main p {color:#778574;font-size:13px;margin:5px 0 0;line-height:1.66;}
.step-min {font-size:11px;color:#da854f;background:#fff0e1;border-radius:100px;padding:4px 9px;white-space:nowrap;}
.macro-grid {display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.nutrition-metric {background:#f6f8ef;border:1px solid #e8ecde;border-radius:15px;padding:16px;margin-bottom:12px;}
.nutrition-metric b {display:block;font-size:24px;color:#385b42;}
.nutrition-metric small {font-size:11px;letter-spacing:.5px;font-weight:800;color:#8d9a83;}
.tip-item {background:#f6f8ef;border-radius:13px;padding:12px 14px;margin:9px 0;color:#60735b;font-size:13px;line-height:1.55;}
.tip-item::before {content:'✦';color:#e58b57;margin-right:9px;}
.small-note {font-size:12px;color:#919b8b;line-height:1.55;}
.flow-row {display:flex;justify-content:space-between;align-items:stretch;gap:8px;flex-wrap:wrap;margin:22px 0;}
.flow-box {flex:1 1 155px;min-width:140px;background:#fffefb;border:1px solid #dfe8d9;border-radius:17px;padding:18px;text-align:center;box-shadow:0 8px 20px #25442408;}
.flow-icon {font-size:27px;margin-bottom:10px;}
.flow-title {font-weight:900;font-size:13px;color:#2b4d36;}
.flow-desc {font-size:11px;color:#879780;line-height:1.5;margin-top:6px;}
.flow-arrow {display:flex;align-items:center;justify-content:center;color:#d58654;font-size:24px;font-weight:900;}
@media (max-width:900px) {.hero {min-height:280px;padding:28px 26px;background-image:linear-gradient(90deg,#244934eb,#244934a9),url('https://images.unsplash.com/photo-1680359869958-fbdf77a5cbc0?auto=format&fit=crop&w=1200&q=70');}.hero h1{font-size:35px;} [data-testid="stMainBlockContainer"],.main .block-container{padding:1.25rem 1rem 4rem;} .flow-arrow{display:none;}}
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)

# Keep session variables in Streamlit, not in mutable global state.
st.session_state.setdefault("ingredients_text", "Tomato\nOnion\nPaneer\nCapsicum")
st.session_state.setdefault("latest_recipe", None)
st.session_state.setdefault("last_id", None)
st.session_state.setdefault("last_is_demo", False)


with st.sidebar:
    st.markdown('''<div class="brand-logo"><div class="brand-mark">🍋</div><div><div class="brand-name">Savour<span style="color:#e87947">AI</span></div><div class="brand-sub">THE RECIPE STUDIO</div></div></div>''', unsafe_allow_html=True)
    st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
    installed_models = []
    ollama_problem = None
    try:
        installed_models = list_local_models()
        if installed_models:
            st.markdown('<div class="side-pill side-ok">● &nbsp; Ollama connected · Local AI ready</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="side-pill side-miss">● &nbsp; No local models downloaded</div>', unsafe_allow_html=True)
            st.caption("Open PowerShell and run: `ollama pull llama3.2`")
    except RecipeAIError as exc:
        ollama_problem = str(exc)
        st.markdown('<div class="side-pill side-miss">● &nbsp; Ollama is not connected</div>', unsafe_allow_html=True)
        st.caption(ollama_problem)

    preferred_model = model_name()
    if installed_models:
        selected_model = st.selectbox(
            "🤖 Local Ollama model",
            options=installed_models,
            index=(installed_models.index(preferred_model) if preferred_model in installed_models else next((i for i, name in enumerate(installed_models) if name.split(":")[0] == preferred_model.split(":")[0]), 0)),
            help="Choose a model already downloaded with ollama pull. All requests stay on this PC.",
        )
    else:
        selected_model = preferred_model
        st.caption(f"Configured model: `{selected_model}`")

    with st.expander("🔌 Test local Ollama connection"):
        st.caption("Checks the local Ollama service and whether your selected model is installed. No API key required.")
        if st.button("Check Ollama", key="ollama_connection_test", use_container_width=True):
            try:
                st.success(check_ollama_connection(selected_model))
            except RecipeAIError as exc:
                st.error(str(exc))
        st.code("ollama pull llama3.2", language="powershell")
    st.markdown('<div class="side-heading">MAKE IT YOURS</div>', unsafe_allow_html=True)
    cuisine = st.selectbox("🌍 Cuisine", ["Surprise me", "Indian", "Italian", "Asian fusion", "Mediterranean", "Mexican", "Continental"], index=1)
    diet = st.selectbox("🥬 Dietary preference", ["Any", "Vegetarian", "Vegan", "Egg-free", "Dairy-free", "Gluten-free"], index=1)
    servings = st.select_slider("🍽️ Servings", options=[1, 2, 3, 4, 5, 6, 7, 8], value=2)
    max_minutes = st.select_slider("⏱️ Total cooking time", options=[15, 20, 30, 40, 50, 60, 90], value=40, format_func=lambda n: f"{n} min")
    spice = st.select_slider("🌶️ Spice level", options=["Mild", "Medium", "Hot"], value="Medium")
    avoid = st.text_input("🚫 Avoid ingredients (optional)", placeholder="e.g. peanuts, mushrooms")
    st.markdown('<div class="side-tip"><strong>💡 Your kitchen, your recipe</strong>Use fresh ingredients you already have. Basic items like salt or oil may be suggested, but anything extra will be labeled clearly.</div>', unsafe_allow_html=True)
    try:
        history_count = len(list_recipes())
    except Exception:
        history_count = 0
    try:
        st.caption(f"📚 {history_count} saved recipes · 🤖 Local model: {selected_model}")
    except RecipeAIError as exc:
        st.warning(str(exc))


st.markdown('''<section class="hero"><div class="hero-copy">
  <div class="hero-eyebrow">✦ YOUR PERSONAL AI SOUS-CHEF</div>
  <h1>Good food starts with<br><em>what you already have.</em></h1>
  <p>Just tell us what's in your fridge. Our five-step AI chef will turn simple ingredients into a meal worth making.</p>
  <div class="hero-chips"><span class="hero-chip">✳ 5 intelligent steps</span><span class="hero-chip">⌛ Made for busy cooks</span><span class="hero-chip">♡ Made just for you</span></div>
</div></section>''', unsafe_allow_html=True)


def render_result(state: dict, *, key: str = "latest", sample: bool = False) -> None:
    recipe = state.get("recipe") or {}
    nutrition = state.get("nutrition") or {}
    tips = state.get("tips") or {}
    recipe_title = h(recipe.get("recipe_name", "Your Recipe"))
    description = h(recipe.get("description", "Made from ingredients you already have."))
    sample_label = "SAMPLE PREVIEW" if sample else "FRESHLY GENERATED FOR YOU"
    st.markdown(f'''<div class="result-banner"><div class="result-eyebrow">✦ {sample_label}</div><h2>{recipe_title}</h2><p>{description}</p></div>''', unsafe_allow_html=True)

    total_time = int(positive_number(recipe.get("prep_time_minutes"), 0) + positive_number(recipe.get("cook_time_minutes"), 0))
    stat_data = [
        ("TIME", f"{total_time} min", "⏱"),
        ("SERVINGS", str(recipe.get("servings", state.get("servings", 2))), "🍽"),
        ("DIFFICULTY", h(recipe.get("difficulty", "Easy")), "🌿"),
        ("CALORIES / SERVING", f"~{h(nutrition.get('calories_per_serving', '—'))} kcal", "⚡"),
    ]
    cols = st.columns(4, gap="small")
    for col, (label, value, icon) in zip(cols, stat_data):
        with col:
            st.markdown(f'<div class="stat-tile"><div class="stat-label">{icon} &nbsp; {label}</div><div class="stat-value">{value}</div></div>', unsafe_allow_html=True)

    left, right = st.columns([0.94, 1.45], gap="large")
    with left:
        rows = []
        for entry in recipe.get("ingredients", []):
            if isinstance(entry, dict):
                amount = h(entry.get("quantity", ""))
                name = h(entry.get("item", ""))
                missing = '' if entry.get("available", True) else '<span class="ing-missing">NEED TO GET</span>'
                rows.append(f'<div class="ing-row"><div class="ing-dot"></div><div><strong>{amount}</strong> {name}</div>{missing}</div>')
            else:
                rows.append(f'<div class="ing-row"><div class="ing-dot"></div>{h(entry)}</div>')
        st.markdown('<div class="content-card"><h3>🥕 What you’ll need</h3>' + "".join(rows) + '</div>', unsafe_allow_html=True)
        if recipe.get("missing_ingredients"):
            st.info("Optional or missing items: " + ", ".join(map(str, recipe["missing_ingredients"])))
        notes = state.get("analyzed", {}).get("ingredient_notes", [])
        if notes:
            st.markdown('<div class="content-card"><h3>🌿 Ingredient insights</h3>' + "".join(f'<div class="tip-item">{h(n)}</div>' for n in notes[:4]) + '</div>', unsafe_allow_html=True)
    with right:
        steps_html = []
        for i, step in enumerate(recipe.get("steps", []), 1):
            if isinstance(step, dict):
                title, detail, minutes = h(step.get("title", f"Step {i}")), h(step.get("detail", "")), step.get("minutes", "")
            else:
                title, detail, minutes = f"Step {i}", h(step), ""
            time_html = f'<span class="step-min">{h(minutes)} min</span>' if minutes else ''
            steps_html.append(f'<div class="step-row"><span class="step-number">{i:02}</span><div class="step-main"><strong>{title}</strong><p>{detail}</p></div>{time_html}</div>')
        st.markdown('<div class="content-card"><h3>👩‍🍳 Let’s get cooking</h3>' + "".join(steps_html) + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker" style="margin-top:10px">GOOD TO KNOW</div><div class="section-title" style="font-size:25px">Nutrition & little chef secrets</div>', unsafe_allow_html=True)
    nutrition_col, tips_col = st.columns([0.95, 1.35], gap="large")
    with nutrition_col:
        metrics = [("Protein", "protein_g"), ("Carbs", "carbs_g"), ("Fat", "fat_g"), ("Fiber", "fiber_g")]
        metric_html = "".join(
            f'<div class="nutrition-metric"><b>{h(nutrition.get(item, "—"))} g</b><small>{label.upper()}</small></div>'
            for label, item in metrics
        )
        allergen_html = (
            '<p class="small-note"><strong>Possible allergens:</strong> '
            + ", ".join(h(x) for x in nutrition.get("potential_allergens", [])) + '</p>'
            if nutrition.get("potential_allergens") else ''
        )
        st.markdown(
            '<div class="content-card"><h3>🥗 Estimated nutrition</h3>'
            '<p class="small-note">Approximate values per serving, based on the generated recipe.</p>'
            '<div class="macro-grid">' + metric_html + '</div>'
            '<p class="small-note">⚠️ AI-generated estimates are approximate, not measured nutrition data.</p>'
            + allergen_html + '</div>', unsafe_allow_html=True,
        )
    with tips_col:
        items = "".join(f'<div class="tip-item">{h(t)}</div>' for t in tips.get("chef_tips", []))
        extras = "".join(
            f'<p class="small-note"><strong>{h(label)}:</strong> {h(tips.get(field))}</p>'
            for label, field in [("To serve", "serving_suggestion"), ("Store it", "storage_tip"), ("Swap it", "swap_idea"), ("Food safety", "food_safety_note")]
            if tips.get(field)
        )
        st.markdown(f'<div class="content-card"><h3>✨ Chef’s little secrets</h3>{items}{extras}</div>', unsafe_allow_html=True)
    st.download_button(
        "⬇️ Download recipe as Markdown",
        data=export_markdown(state),
        file_name="savourai_" + "".join(c if c.isalnum() else "_" for c in recipe.get("recipe_name", "recipe").lower())[:50] + ".md",
        mime="text/markdown",
        key=f"download_{key}",
        use_container_width=True,
    )


def sample_recipe_state() -> dict:
    """Clearly labeled offline UI preview that does not invoke Ollama."""
    return {
        "raw_ingredients": "Tomato, Onion, Paneer, Capsicum",
        "ingredients": ["Tomato", "Onion", "Paneer", "Capsicum"],
        "cuisine": "Indian", "diet": "Vegetarian", "servings": 2,
        "analyzed": {"ingredient_notes": ["Paneer makes the dish creamy and satisfying.", "Bell peppers add sweetness and texture."]},
        "recipe": {
            "recipe_name": "Golden Paneer & Pepper Skillet",
            "description": "Tender paneer and colorful peppers in a cozy tomato-onion masala. A bright, weeknight-friendly dish.",
            "cuisine": "Indian", "difficulty": "Easy", "prep_time_minutes": 10,
            "cook_time_minutes": 20, "servings": 2,
            "ingredients": [
                {"item": "Paneer", "quantity": "200 g", "available": True},
                {"item": "Tomatoes", "quantity": "2 medium", "available": True},
                {"item": "Onion", "quantity": "1 medium", "available": True},
                {"item": "Capsicum", "quantity": "1 medium", "available": True},
                {"item": "Oil", "quantity": "1 tbsp", "available": False},
                {"item": "Salt & mild spices", "quantity": "to taste", "available": False},
            ],
            "steps": [
                {"title": "Get everything ready", "detail": "Chop the tomatoes, onion and capsicum. Cut the paneer into bite-sized pieces.", "minutes": 5},
                {"title": "Build a fragrant base", "detail": "Warm the oil in a pan and cook the onion until softened. Add tomatoes and cook until saucy.", "minutes": 9},
                {"title": "Add peppers and paneer", "detail": "Stir in capsicum and a little seasoning. Add paneer and gently cook until everything is heated through.", "minutes": 8},
                {"title": "Finish and serve", "detail": "Taste for seasoning and serve warm with rice or roti if available.", "minutes": 3},
            ],
            "missing_ingredients": ["Oil", "Salt & mild spices"],
        },
        "nutrition": {"calories_per_serving": 345, "protein_g": 21, "carbs_g": 15, "fat_g": 23, "fiber_g": 4, "potential_allergens": ["Milk (paneer)"]},
        "tips": {
            "chef_tips": ["Pat the paneer dry before adding it for a better texture.", "Keep the peppers slightly crisp for a fresh bite.", "Add a squeeze of lemon if you have one."],
            "serving_suggestion": "Great with warm roti or rice.",
            "storage_tip": "Cool promptly and refrigerate leftovers in a sealed container.",
            "swap_idea": "Try firm tofu in place of paneer if desired.",
            "food_safety_note": "Heat the dish thoroughly before eating and refrigerate leftovers promptly.",
        },
        "trace": ["Available Ingredients", "Ingredient Analyzer", "Recipe Generator", "Nutrition Advisor", "Cooking Tips Generator"],
    }


make_tab, library_tab, flow_tab = st.tabs(["🍳 Create a recipe", "📖 My recipe book", "🧠 The AI workflow"])

with make_tab:
    left, right = st.columns([1.08, 0.91], gap="large")
    with left:
        st.markdown('<div class="section-kicker">01 / START HERE</div><div class="section-title">What’s in your kitchen?</div><div class="section-desc">List your ingredients. Our AI chef will take care of the rest.</div>', unsafe_allow_html=True)
        st.markdown('<div class="quick-help">NEED AN IDEA? TRY A QUICK START</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3, gap="small")
        with p1:
            if st.button("🧀 Paneer night", use_container_width=True):
                st.session_state.ingredients_text = "Tomato\nOnion\nPaneer\nCapsicum"
                st.rerun()
        with p2:
            if st.button("🥗 Veggie meal", use_container_width=True):
                st.session_state.ingredients_text = "Spinach\nChickpeas\nTomato\nCucumber\nLemon"
                st.rerun()
        with p3:
            if st.button("🍝 Pasta fix", use_container_width=True):
                st.session_state.ingredients_text = "Pasta\nTomato\nGarlic\nCapsicum\nCheese"
                st.rerun()
        with st.form("ingredients_form"):
            st.text_area("Available ingredients", key="ingredients_text", height=185, help="Enter one ingredient per line, or use commas.", placeholder="Tomato\nOnion\nPaneer\nCapsicum")
            submit = st.form_submit_button("✨ Generate my recipe", use_container_width=True, type="primary")
        if st.button("👀 Preview recipe design (no model needed)", use_container_width=True, key="sample_preview"):
            st.session_state.latest_recipe = sample_recipe_state()
            st.session_state.last_is_demo = True
            st.session_state.last_id = None
        st.caption("🔒 AI runs on your PC via Ollama (localhost). No API key. Recipes are saved locally.")
    with right:
        st.markdown('''<div class="inspo"><div class="inspo-img"><span class="inspo-tag">✦ TONIGHT’S INSPIRATION</span></div>
          <div class="inspo-copy"><div class="inspo-kicker">SIMPLE INGREDIENTS. BEAUTIFUL RESULTS.</div>
          <h3>Something delicious is waiting.</h3>
          <p>Tomato, onion, paneer & peppers can become a vibrant, cozy dinner. Choose a starter above, or make something completely your own.</p>
          <div class="inspo-badges"><span class="inspo-badge">🌶 Custom spice</span><span class="inspo-badge">🍽 Portions</span><span class="inspo-badge">⚡ AI powered</span></div>
          </div></div>''', unsafe_allow_html=True)

    if submit:
        if not installed_models or ollama_problem:
            st.error(ollama_problem or "No local Ollama models found. Run `ollama pull llama3.2` in PowerShell, then refresh this page.")
        else:
            labels = {
                "available_ingredients": "Organizing your ingredients",
                "ingredient_analyzer": "Exploring your ingredient combinations",
                "recipe_generator": "Designing a delicious recipe",
                "nutrition_advisor": "Estimating nutrition per serving",
                "cooking_tips_generator": "Adding the finishing chef tips",
            }
            progress = st.progress(0.01, text="Your chef is getting ready…")
            try:
                from workflow import run_agent, NODE_NAMES
                def update_progress(node: str, current_state: dict) -> None:
                    idx = NODE_NAMES.index(node)
                    progress.progress((idx + 1) / len(NODE_NAMES), text=f"{idx + 1}/5 · {labels[node]}")

                state = run_agent({
                    "raw_ingredients": st.session_state.ingredients_text,
                    "cuisine": cuisine,
                    "diet": diet,
                    "servings": servings,
                    "max_minutes": max_minutes,
                    "spice": spice,
                    "avoid": avoid,
                }, on_progress=update_progress, ask=partial(ask_ollama_json, model=selected_model))
                st.session_state.latest_recipe = state
                st.session_state.last_is_demo = False
                try:
                    st.session_state.last_id = save_recipe(state)
                    st.toast("Recipe created & added to your recipe book!", icon="✅")
                except Exception:
                    st.session_state.last_id = None
                    st.warning("Recipe created, but could not save it to SQLite. You can still download it below.")
            except (RecipeAIError, RecipeInputError, ValueError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("The recipe agent hit an unexpected error. Check the terminal for technical details.")
                import traceback
                traceback.print_exc()
            finally:
                progress.empty()

    if st.session_state.latest_recipe is not None:
        st.divider()
        render_result(st.session_state.latest_recipe, key="latest", sample=st.session_state.last_is_demo)

with library_tab:
    st.markdown('<div class="section-kicker">YOUR PERSONAL COOKBOOK</div><div class="section-title">Recipes worth keeping.</div><div class="section-desc">Your previous creations are saved on this computer. You can revisit, favorite, or delete them.</div>', unsafe_allow_html=True)
    try:
        records = list_recipes()
    except Exception:
        records = []
        st.error("Could not open the local recipe history database.")
    if not records:
        st.info("🍲 Your recipe book is empty. Generate your first recipe in the Create a recipe tab!")
    else:
        only_favs = st.checkbox("⭐ Favorites only", value=False)
        visible = [r for r in records if r["favorite"]] if only_favs else records
        if not visible:
            st.info("You haven't favorited any recipes yet.")
        else:
            id_to_record = {r["id"]: r for r in visible}
            selected = st.selectbox("Choose a saved recipe", [r["id"] for r in visible], format_func=lambda rid: ("⭐ " if id_to_record[rid]["favorite"] else "🍲 ") + id_to_record[rid]["name"] + "  ·  " + id_to_record[rid]["created_at"][:10])
            chosen = id_to_record[selected]
            fav_col, remove_col = st.columns(2, gap="small")
            with fav_col:
                if st.button("☆ Remove favorite" if chosen["favorite"] else "⭐ Add to favorites", use_container_width=True, key="fav_button"):
                    set_favorite(selected, not bool(chosen["favorite"]))
                    st.rerun()
            with remove_col:
                if st.button("🗑️ Delete saved recipe", use_container_width=True, key="delete_button"):
                    delete_recipe(selected)
                    st.rerun()
            chosen_state = get_recipe(selected)
            if chosen_state:
                render_result(chosen_state, key="saved")

with flow_tab:
    st.markdown('<div class="section-kicker">HOW THE MAGIC HAPPENS</div><div class="section-title">Five minds. One delicious meal.</div><div class="section-desc">A real LangGraph StateGraph runs five connected nodes. Each node builds on the previous result using shared typed state.</div>', unsafe_allow_html=True)
    nodes = [
        ("🥬", "Available Ingredients", "Validates and cleans your input"),
        ("🔎", "Ingredient Analyzer", "Checks combinations & pantry needs"),
        ("🍲", "Recipe Generator", "Creates the dish and cooking steps"),
        ("🥗", "Nutrition Advisor", "Estimates per-serving nutrition"),
        ("✨", "Cooking Tips", "Adds practical chef-level guidance"),
    ]
    parts = []
    for i, (icon, title, subtitle) in enumerate(nodes):
        if i:
            parts.append('<div class="flow-arrow">→</div>')
        parts.append(f'<div class="flow-box"><div class="flow-icon">{icon}</div><div class="flow-title">{title}</div><div class="flow-desc">{subtitle}</div></div>')
    st.markdown('<div class="flow-row">' + "".join(parts) + '</div>', unsafe_allow_html=True)
    st.success("✅ Exactly 5 LangGraph nodes. The first node validates input; the next four use local Ollama AI.")
    st.code('''START → available_ingredients → ingredient_analyzer → recipe_generator
      → nutrition_advisor → cooking_tips_generator → END''', language="text")
    with st.expander("What happens at each stage?"):
        st.markdown("""1. **Available Ingredients:** Cleans and de-duplicates typed ingredient names.\n2. **Ingredient Analyzer:** Finds practical combinations and optional pantry basics.\n3. **Recipe Generator:** Produces a named dish, ingredient quantities and cooking steps.\n4. **Nutrition Advisor:** Estimates calories and macronutrients per serving; values are approximate.\n5. **Cooking Tips Generator:** Adds chef tips, serving ideas, storage information and a safety note.""")
    st.info("The recipe is generated via Ollama, not from a fixed list of meals. Ingredients and recipe preferences are processed locally by Ollama only when you click Generate.")

st.markdown('<div style="text-align:center;color:#99a596;font-size:11px;padding-top:40px;">MADE WITH 🍋 &nbsp; SAVOURAI · LANGGRAPH × OLLAMA · YOUR KITCHEN, YOUR RULES</div>', unsafe_allow_html=True)
