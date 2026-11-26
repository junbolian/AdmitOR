# IR: {"sets":{"products":["I","II","III"],"A":["A1","A2"],"B":["B1","B2","B3"],"eligible":[["A1","I"],["A1","II"],["A2","I"],["A2","II"],["A2","III"],["B1","I"],["B1","II"],["B2","I"],["B2","III"],["B3","I"]]},"params":{"processing_time[e,p]":"params[time_<e>_<p>] for eligible pairs","capacity[e]":"params[cap_<e>]","full_load_cost[e]":"params[cost_<e>]","raw_cost[p]":"params[raw_<p>]","selling_price[p]":"params[price_<p>]"},"variables":{"production[p]":"NonNegativeReals","processed[e,p]":"NonNegativeReals for eligible pairs"},"constraints":["For each product p: sum(processed[e,p] for eligible A equipment e) = production[p].","For each product p: sum(processed[e,p] for eligible B equipment e) = production[p].","For each equipment e: sum(processing_time[e,p]*processed[e,p] for eligible products p) <= capacity[e]."],"objective":"Maximize sum((selling_price[p]-raw_cost[p])*production[p]) - sum(full_load_cost[e]/capacity[e]*sum(processing_time[e,p]*processed[e,p] for eligible products p)); equipment costs are proportional to operating-time utilization."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("I", "II", "III")
    equipment_a = ("A1", "A2")
    equipment_b = ("B1", "B2", "B3")
    equipment = equipment_a + equipment_b
    eligible_pairs = (
        ("A1", "I"),
        ("A1", "II"),
        ("A2", "I"),
        ("A2", "II"),
        ("A2", "III"),
        ("B1", "I"),
        ("B1", "II"),
        ("B2", "I"),
        ("B2", "III"),
        ("B3", "I"),
    )

    processing_times = {
        ("A1", "I"): params["time_A1_I"],
        ("A1", "II"): params["time_A1_II"],
        ("A2", "I"): params["time_A2_I"],
        ("A2", "II"): params["time_A2_II"],
        ("A2", "III"): params["time_A2_III"],
        ("B1", "I"): params["time_B1_I"],
        ("B1", "II"): params["time_B1_II"],
        ("B2", "I"): params["time_B2_I"],
        ("B2", "III"): params["time_B2_III"],
        ("B3", "I"): params["time_B3_I"],
    }
    capacities = {
        "A1": params["cap_A1"],
        "A2": params["cap_A2"],
        "B1": params["cap_B1"],
        "B2": params["cap_B2"],
        "B3": params["cap_B3"],
    }
    full_load_costs = {
        "A1": params["cost_A1"],
        "A2": params["cost_A2"],
        "B1": params["cost_B1"],
        "B2": params["cost_B2"],
        "B3": params["cost_B3"],
    }
    raw_costs = {
        "I": params["raw_I"],
        "II": params["raw_II"],
        "III": params["raw_III"],
    }
    selling_prices = {
        "I": params["price_I"],
        "II": params["price_II"],
        "III": params["price_III"],
    }

    # A full-load cost requires a strictly positive reference capacity.
    if any(capacities[equip] <= 0 for equip in equipment):
        return {"objective": None, "status": "invalid_capacity"}

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=products, ordered=True)
    model.equipment_a = pyo.Set(initialize=equipment_a, ordered=True)
    model.equipment_b = pyo.Set(initialize=equipment_b, ordered=True)
    model.equipment = pyo.Set(initialize=equipment, ordered=True)
    model.eligible_pairs = pyo.Set(
        dimen=2, initialize=eligible_pairs, ordered=True
    )

    model.processing_time = pyo.Param(
        model.eligible_pairs,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.equipment,
        initialize=capacities,
        within=pyo.PositiveReals,
    )
    model.full_load_cost = pyo.Param(
        model.equipment,
        initialize=full_load_costs,
        within=pyo.NonNegativeReals,
    )
    model.raw_cost = pyo.Param(
        model.products,
        initialize=raw_costs,
        within=pyo.NonNegativeReals,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize=selling_prices,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.processed = pyo.Var(
        model.eligible_pairs, domain=pyo.NonNegativeReals
    )

    def balance_a_rule(current_model, product):
        return sum(
            current_model.processed[equip, product]
            for equip in current_model.equipment_a
            if (equip, product) in current_model.eligible_pairs
        ) == current_model.production[product]

    def balance_b_rule(current_model, product):
        return sum(
            current_model.processed[equip, product]
            for equip in current_model.equipment_b
            if (equip, product) in current_model.eligible_pairs
        ) == current_model.production[product]

    def operating_time_rule(current_model, equip):
        return sum(
            current_model.processing_time[equip, product]
            * current_model.processed[equip, product]
            for product in current_model.products
            if (equip, product) in current_model.eligible_pairs
        )

    def equipment_capacity_rule(current_model, equip):
        return (
            current_model.operating_time[equip]
            <= current_model.capacity[equip]
        )

    model.balance_a = pyo.Constraint(
        model.products, rule=balance_a_rule
    )
    model.balance_b = pyo.Constraint(
        model.products, rule=balance_b_rule
    )
    model.operating_time = pyo.Expression(
        model.equipment, rule=operating_time_rule
    )
    model.equipment_capacity = pyo.Constraint(
        model.equipment, rule=equipment_capacity_rule
    )

    model.profit = pyo.Objective(
        expr=sum(
            (model.selling_price[product] - model.raw_cost[product])
            * model.production[product]
            for product in model.products
        )
        - sum(
            model.full_load_cost[equip]
            * model.operating_time[equip]
            / model.capacity[equip]
            for equip in model.equipment
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}