from enum import Enum


class Ingredient(Enum):
    POTATO = "potato"
    # Later: ONION, TOMATO, etc.


class Order:
    def __init__(self, order_id: int, order_name: str, ingredients: dict[Ingredient, float]):
        """
        ingredients: dict of Ingredient -> grams required
        """
        self.order_id = order_id
        self.order_name = order_name
        self.ingredients = ingredients

    def __repr__(self):
        formatted = {ing.value: f"{amt}g" for ing, amt in self.ingredients.items()}
        return f"{self.order_name}"


class DummyOrderManager:
    def __init__(self):
        self.orders: list[Order] = []
        self.next_order_id = 1
        self.ingredient_totals: dict[Ingredient, float] = {}

    # ----------------------------------------------------------------------
    # Add order
    # ----------------------------------------------------------------------
    def add_order(self, order_name: str, ingredients: dict[Ingredient, float]):
        """Add an order and update ingredient totals efficiently."""
        order = Order(self.next_order_id, order_name, ingredients)
        self.next_order_id += 1
        self.orders.append(order)

        # Increment totals directly
        for ingredient, grams in ingredients.items():
            self.ingredient_totals[ingredient] = self.ingredient_totals.get(ingredient, 0.0) + grams

        print(f"[OrderManager] Added {order}")

    # ----------------------------------------------------------------------
    # Remove order
    # ----------------------------------------------------------------------
    def remove_order(self, index: int):
        """Remove an order by index and decrement ingredient totals."""
        if 0 <= index < len(self.orders):
            removed = self.orders.pop(index)

            for ingredient, grams in removed.ingredients.items():
                if ingredient in self.ingredient_totals:
                    self.ingredient_totals[ingredient] -= grams
                    if self.ingredient_totals[ingredient] <= 0:
                        del self.ingredient_totals[ingredient]

            print(f"[OrderManager] Removed {removed}")
        else:
            print(f"[OrderManager] Invalid order index: {index}")

    # ----------------------------------------------------------------------
    # Accessors
    # ----------------------------------------------------------------------
    def get_pending_orders(self):
        """Return all pending orders."""
        return list(self.orders)

    def get_ingredients(self):
        """Return current total ingredient requirements in grams."""
        return dict(self.ingredient_totals)
