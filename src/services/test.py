def get_categories():
    categories = [{'_id': 1245, 'title': 'Grill'}, {'_id': 145, 'title': 'Pooop'}]
    categories = {categories[i]['_id']: categories[i]['title'] for i in range(len(categories))}
    return categories


print(get_categories())