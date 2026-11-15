"""Integration against a real LangGraph StateGraph, but mocked local Ollama responses."""
import pytest
pytest.importorskip('langgraph')

from workflow import NODE_NAMES, build_graph, run_agent


def fake_ollama(system: str, payload: dict, *, max_tokens: int) -> dict:
    if 'INGREDIENT ANALYZER' in system:
        return {'usable_ingredients': payload['provided_ingredients'], 'pantry_basics':['salt','oil'], 'flavour_profile':'savory', 'ingredient_notes':['Paneer pairs with tomato'], 'potential_allergens':['milk']}
    if 'RECIPE GENERATOR' in system:
        return {'recipe_name':'Paneer & Pepper Skillet', 'description':'A cozy weekday dinner', 'cuisine':'Indian', 'difficulty':'Easy', 'prep_time_minutes':10, 'cook_time_minutes':20, 'servings':2, 'ingredients':[{'item':'Paneer','quantity':'200 g','available':True},{'item':'Capsicum','quantity':'1','available':True}], 'steps':[{'title':'Prepare','detail':'Chop vegetables.','minutes':5},{'title':'Cook','detail':'Simmer until cooked.','minutes':20}], 'missing_ingredients':[], 'why_it_works':'fresh flavors'}
    if 'NUTRITION ADVISOR' in system:
        return {'calories_per_serving':350, 'protein_g':19, 'carbs_g':12, 'fat_g':21, 'fiber_g':4, 'nutrition_note':'rough estimate', 'potential_allergens':['milk']}
    if 'COOKING TIPS GENERATOR' in system:
        return {'chef_tips':['Finish with coriander', 'Serve warm', 'Season to taste'], 'serving_suggestion':'Enjoy with roti', 'storage_tip':'Refrigerate promptly', 'swap_idea':'Try tofu', 'food_safety_note':'Cook thoroughly'}
    raise AssertionError('Unexpected node prompt')


def test_has_exactly_five_nodes():
    graph = build_graph(ask=fake_ollama)
    names = set(graph.get_graph().nodes)
    assert set(NODE_NAMES).issubset(names)
    assert len([n for n in names if n not in ('__start__','__end__')]) == 5


def test_graph_end_to_end_with_fake_ollama():
    called = []
    result = run_agent({'raw_ingredients':'Tomato, Onion\nPaneer\nCapsicum', 'cuisine':'Indian', 'diet':'Vegetarian', 'servings':2, 'max_minutes':40, 'spice':'Medium', 'avoid':'peanut'}, on_progress=lambda n, _: called.append(n), ask=fake_ollama)
    assert called == NODE_NAMES
    assert result['trace'] == ['Available Ingredients', 'Ingredient Analyzer', 'Recipe Generator', 'Nutrition Advisor', 'Cooking Tips Generator']
    assert result['ingredients'] == ['Tomato','Onion','Paneer','Capsicum']
    assert result['recipe']['recipe_name'] == 'Paneer & Pepper Skillet'
    assert result['nutrition']['calories_per_serving'] == 350
    assert len(result['tips']['chef_tips']) == 3
