# IR: {"sets":{"products":["I","II","III"],"quarters":[1,2,3,4]},"params":["production_hours_per_quarter","hours_per_unit_I","hours_per_unit_II","hours_per_unit_III","orders_I","orders_II","orders_III","ending_inventory_required","compensation_per_unit_per_quarter_I_II","compensation_per_unit_per_quarter_III","storage_fee_per_unit_per_quarter"],"input_convention":"orders_I, orders_II, and orders_III are sequences in quarter order","variables":{"production[product,quarter]":"NonNegativeReals","inventory[product,quarter]":"NonNegativeReals, end-of-quarter stock","backlog[product,quarter]":"NonNegativeReals, end-of-quarter overdue orders"},"constraints":["For each quarter: sum(hours_per_unit[product]*production[product,quarter]) <= production_hours_per_quarter.","For each product and quarter: inventory[product,quarter]-backlog[product,quarter] = previous_inventory-previous_backlog+production[product,quarter]-orders[product,quarter], with initial inventory and backlog zero.","production[I,2] = 0.","For each product: inventory[product,4] = ending_inventory_required.","For each product: backlog[product,4] = 0."],"objective":"Minimize sum over all products and quarters of compensation_rate[product]*backlog[product,quarter] + storage_fee_per_unit_per_quarter*inventory[product,quarter], including fourth-quarter ending inventory."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("I", "II", "III")
    quarters = (1, 2, 3, 4)

    production_hours = params["production_hours_per_quarter"]
    hours_per_unit = {
        "I": params["hours_per_unit_I"],
        "II": params["hours_per_unit_II"],
        "III": params["hours_per_unit_III"],
    }
    order_sequences = {
        "I": params["orders_I"],
        "II": params["orders_II"],
        "III": params["orders_III"],
    }
    ending_inventory = params["ending_inventory_required"]
    compensation_I_II = params[
        "compensation_per_unit_per_quarter_I_II"
    ]
    compensation_III = params[
        "compensation_per_unit_per_quarter_III"
    ]
    storage_fee = params["storage_fee_per_unit_per_quarter"]

    orders = {
        (product, quarter): order_sequences[product][quarter - 1]
        for product in products
        for quarter in quarters
    }
    compensation = {
        "I": compensation_I_II,
        "II": compensation_I_II,
        "III": compensation_III,
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.quarters = pyo.Set(initialize=quarters, ordered=True)

    model.production = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.backlog = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )

    def capacity_rule(block, quarter):
        return sum(
            hours_per_unit[product] * block.production[product, quarter]
            for product in products
        ) <= production_hours

    model.production_capacity = pyo.Constraint(
        model.quarters, rule=capacity_rule
    )

    def balance_rule(block, product, quarter):
        previous_inventory = (
            0 if quarter == 1 else block.inventory[product, quarter - 1]
        )
        previous_backlog = (
            0 if quarter == 1 else block.backlog[product, quarter - 1]
        )
        return (
            block.inventory[product, quarter]
            - block.backlog[product, quarter]
            == previous_inventory
            - previous_backlog
            + block.production[product, quarter]
            - orders[product, quarter]
        )

    model.inventory_backlog_balance = pyo.Constraint(
        model.products, model.quarters, rule=balance_rule
    )

    model.equipment_replacement = pyo.Constraint(
        expr=model.production["I", 2] == 0
    )

    def terminal_inventory_rule(block, product):
        return block.inventory[product, 4] == ending_inventory

    model.required_ending_inventory = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
    )

    def terminal_backlog_rule(block, product):
        return block.backlog[product, 4] == 0

    model.all_orders_completed = pyo.Constraint(
        model.products, rule=terminal_backlog_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            compensation[product] * model.backlog[product, quarter]
            + storage_fee * model.inventory[product, quarter]
            for product in products
            for quarter in quarters
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}