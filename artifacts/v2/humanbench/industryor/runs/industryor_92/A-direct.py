import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ["I", "II", "III"]

    # Processing times by (equipment, product); missing combos are not allowed
    time = {
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

    cap = {
        "A1": params["cap_A1"],
        "A2": params["cap_A2"],
        "B1": params["cap_B1"],
        "B2": params["cap_B2"],
        "B3": params["cap_B3"],
    }

    cost = {
        "A1": params["cost_A1"],
        "A2": params["cost_A2"],
        "B1": params["cost_B1"],
        "B2": params["cost_B2"],
        "B3": params["cost_B3"],
    }

    raw = {
        "I": params["raw_I"],
        "II": params["raw_II"],
        "III": params["raw_III"],
    }
    price = {
        "I": params["price_I"],
        "II": params["price_II"],
        "III": params["price_III"],
    }

    # Feasible (equipment, product) combinations define the decision variables
    routes = list(time.keys())

    model = pyo.ConcreteModel()

    model.x = pyo.Var(routes, domain=pyo.NonNegativeReals)

    # Total amount of each product produced
    def total_expr(p):
        return sum(model.x[route] for route in routes if route[1] == p)

    # Production amount per product must balance across the two procedures.
    # Procedure A total == Procedure B total for each product.
    def product_balance_rule(model, p):
        a_total = sum(model.x[route] for route in routes if route[1] == p and route[0].startswith("A"))
        b_total = sum(model.x[route] for route in routes if route[1] == p and route[0].startswith("B"))
        return a_total == b_total

    model.product_balance = pyo.Constraint(products, rule=product_balance_rule)

    # Equipment capacity constraints
    equipment_list = ["A1", "A2", "B1", "B2", "B3"]

    def cap_rule(model, e):
        return sum(time[route] * model.x[route] for route in routes if route[0] == e) <= cap[e]

    model.equip_cap = pyo.Constraint(equipment_list, rule=cap_rule)

    # Equipment cost scales with operating time used relative to capacity:
    # cost contribution = (cost[e] / cap[e]) * (sum of time used on e)
    # Note: at full load, used time == cap[e], giving cost[e]. Linear in x.
    equipment_cost_expr = sum(
        (cost[e] / cap[e]) * sum(time[route] * model.x[route] for route in routes if route[0] == e)
        for e in equipment_list
    )

    revenue_expr = sum(price[p] * total_expr(p) for p in products)
    raw_cost_expr = sum(raw[p] * total_expr(p) for p in products)

    model.obj = pyo.Objective(
        expr=revenue_expr - raw_cost_expr - equipment_cost_expr,
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}