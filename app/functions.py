
from app.models import User, Preferences, Restaurant, Menu, Dish, Theme
def sort_user_preferences(user_id,menu_id):
    user_preferences = Preferences.query.filter_by(user_id=user_id).first()
    menu = Menu.query.filter_by(id=menu_id).first()
    updated_menu =[]
    for dish in menu.dishes:
        dish = Dish.query.filter_by(id=dish.id).first()
        if user_preferences.is_lactose_intolerant and not dish.is_lactose_free:
            continue
        if  user_preferences.is_halal and not dish.is_halal:
            continue
        if  user_preferences.is_vegan and not dish.is_vegan:
            continue
        if  user_preferences.is_vegetarian and not dish.is_vegetarian:
            continue
        if  user_preferences.is_allergic_to_gluten and not dish.is_allergic_to_gluten:
            continue
        if  user_preferences.is_jain and not dish.is_jain:
            continue
        updated_menu.append(dish)
    return updated_menu

