import pytest
from utils import RecipeInputError, export_markdown, parse_avoid, parse_ingredients, positive_number


def test_ingredient_parse_and_dedupe():
    assert parse_ingredients(' Tomato, Onion; Paneer\nCapsicum\n  onion  ') == ['Tomato', 'Onion', 'Paneer', 'Capsicum']


def test_empty_ingredients():
    with pytest.raises(RecipeInputError, match='at least one'):
        parse_ingredients(' , \n ; ')


def test_too_many_ingredients():
    with pytest.raises(RecipeInputError, match='maximum'):
        parse_ingredients(','.join(f'item{i}' for i in range(26)))


def test_avoid_and_number():
    assert parse_avoid('nuts, soy\n egg') == ['nuts', 'soy', 'egg']
    assert positive_number('45') == 45.0
    assert positive_number('-5') == 0


def test_export_markdown():
    state = {'recipe': {'recipe_name': 'Paneer Delight', 'ingredients': [{'item': 'paneer', 'quantity': '200 g'}], 'steps': [{'title': 'Prepare', 'detail': 'Combine ingredients.'}]}, 'nutrition': {'calories_per_serving': 280}, 'tips': {'chef_tips':['Season gently']}}
    document = export_markdown(state)
    assert '# Paneer Delight' in document
    assert '200 g paneer' in document
    assert '280' in document
    assert 'Season gently' in document
