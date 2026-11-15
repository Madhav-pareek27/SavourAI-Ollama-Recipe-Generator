from storage import save_recipe, get_recipe, list_recipes, set_favorite, delete_recipe


def test_save_list_favorite_delete(tmp_path):
    db = tmp_path / 'new' / 'recipes.db'
    state = {'ingredients':['Tomato', 'Paneer'], 'recipe':{'recipe_name':'Paneer Delight', 'cuisine':'Indian'}}
    rid = save_recipe(state, db)
    records = list_recipes(db)
    assert len(records) == 1
    assert records[0]['name'] == 'Paneer Delight'
    assert get_recipe(rid, db)['ingredients'] == ['Tomato','Paneer']
    set_favorite(rid, True, db)
    assert list_recipes(db)[0]['favorite'] == 1
    delete_recipe(rid, db)
    assert not list_recipes(db)
    assert get_recipe(rid, db) is None
