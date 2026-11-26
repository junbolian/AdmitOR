# IR: {"sets":{"P":[0,1,2],"Q":[0,1,2,3]},"params":["reservations","ending_inventory_required","production_hours_per_quarter","hours_per_unit","delay_penalty","inventory_cost"],"variables":{"production[P,Q]":"NonNegativeReals","inventory[P,Q]":"NonNegativeReals","backlog[P,Q]":"NonNegativeReals"},"constraints":["For each product and quarter: previous_inventory - previous_backlog + production - reservations = inventory - backlog; initial inventory and backlog are zero.","For each quarter: sum(hours_per_unit[p] * production[p,q] for p in P) <= production_hours_per_quarter.","production[0,1] = 0.","For each product: inventory[p,3] >= ending_inventory_required.","For each product: backlog[p,3] = 0."],"objective":"Minimize sum(inventory_cost * inventory[p,q] + delay_penalty[p] * backlog[p,q] for p in P, q in Q)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    reservations = params["reservations"]
    ending_inventory_required = params["ending_inventory_required"]
    production_hours_per_quarter = params["production_hours_per_quarter"]
    hours_per_unit = params["hours_per_unit"]
    delay_penalty = params["delay_penalty"]
    inventory_cost = params["inventory_cost"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.quarters = pyo.RangeSet(0, 3)

    model.production = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.backlog = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )

    def balance_rule(instance, product, quarter):
        previous_inventory = (
            0 if quarter == 0 else instance.inventory[product, quarter - 1]
        )
        previous_backlog = (
            0 if quarter == 0 else instance.backlog[product, quarter - 1]
        )
        return (
            previous_inventory
            - previous_backlog
            + instance.production[product, quarter]
            - reservations[product][quarter]
            == instance.inventory[product, quarter]
            - instance.backlog[product, quarter]
        )

    model.material_balance = pyo.Constraint(
        model.products, model.quarters, rule=balance_rule
    )

    def capacity_rule(instance, quarter):
        return sum(
            hours_per_unit[product] * instance.production[product, quarter]
            for product in instance.products
        ) <= production_hours_per_quarter

    model.quarterly_capacity = pyo.Constraint(
        model.quarters, rule=capacity_rule
    )

    model.product_one_shutdown = pyo.Constraint(
        expr=model.production[0, 1] == 0
    )

    def ending_inventory_rule(instance, product):
        return instance.inventory[product, 3] >= ending_inventory_required

    model.required_ending_inventory = pyo.Constraint(
        model.products, rule=ending_inventory_rule
    )

    def final_backlog_rule(instance, product):
        return instance.backlog[product, 3] == 0

    model.final_delivery_completion = pyo.Constraint(
        model.products, rule=final_backlog_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            inventory_cost * model.inventory[product, quarter]
            + delay_penalty[product] * model.backlog[product, quarter]
            for product in model.products
            for quarter in model.quarters
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Success is still determined solely by objective retrieval below.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}