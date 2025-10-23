from enum import Enum


class Ingredient(Enum):
    POTATO = "potato"
    # Later: ONION, TOMATO, etc.


class Order:
    def __init__(self, order_id: int, order_name: str, ingredients: dict[Ingredient, float]):
        self.order_id = order_id
        self.order_name = order_name
        self.ingredients = ingredients
        self.status = "pending"  # "pending", "in_progress", "completed"

    def mark_in_progress(self):
        self.status = "in_progress"

    def mark_completed(self):
        self.status = "completed"

    def __repr__(self):
        return f"{self.order_name} - {self.status}"


class OrderManager:
    def __init__(self):
        self.orders: list[Order] = []
        self.next_order_id = 1
        self.ingredient_totals: dict[Ingredient, float] = {}

    # ----------------------------------------------------------------------
    # Add order
    # ----------------------------------------------------------------------
    def add_order(self, order_name: str, ingredients: dict[Ingredient, float]):
        order = Order(self.next_order_id, order_name, ingredients)
        self.next_order_id += 1
        self.orders.append(order)

        # Update total ingredient requirements
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
        """Return all pending or in-progress orders (not completed)."""
        return [o for o in self.orders if o.status != "completed"]

    def get_ingredients(self):
        return dict(self.ingredient_totals)
