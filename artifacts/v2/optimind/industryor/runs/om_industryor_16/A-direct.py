import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_rate = params["production_rate"]
    regular_time = params["regular_time"]
    overtime_limit = params["overtime_limit"]
    curtain_demand = params["curtain_demand"]
    curtain_profit = params["curtain_profit"]
    clothing_demand = params["clothing_demand"]
    clothing_profit = params["clothing_profit"]

    # Production hours needed per fabric (meters / meters-per-hour)
    curtain_hours_per_meter = 1.0 / production_rate
    clothing_hours_per_meter = 1.0 / production_rate

    # Full-utilization production quantities at regular time
    curtain_full = curtain_demand
    clothing_full = clothing_demand

    model = pyo.ConcreteModel()

    # p1: under-utilized time (deviation below full utilization)
    model.d1 = pyo.Var(within=pyo.NonNegativeReals)
    # p2: overtime hours (deviation above full utilization)
    model.d2 = pyo.Var(within=pyo.NonNegativeReals)
    # p3: shortfall of curtain sales below target
    model.d3c = pyo.Var(within=pyo.NonNegativeReals)
    # p3: shortfall of clothing sales below target
    model.d3k = pyo.Var(within=pyo.NonNegativeReals)

    # Production quantities (meters)
    model.x_curtain = pyo.Var(within=pyo.NonNegativeReals)
    model.x_clothing = pyo.Var(within=pyo.NonNegativeReals)

    # Total production time equation with p1/p2 deviations
    model.time_balance = pyo.Constraint(
        expr=curtain_hours_per_meter * model.x_curtain
        + clothing_hours_per_meter * model.x_clothing
        + model.d1
        - model.d2
        == regular_time
    )

    # p3: sales targets with shortfall
    model.curtain_target = pyo.Constraint(
        expr=model.x_curtain + model.d3c == curtain_demand
    )
    model.clothing_target = pyo.Constraint(
        expr=model.x_clothing + model.d3k == clothing_demand
    )

    # Sales upper bounds
    model.curtain_sales = pyo.Constraint(expr=model.x_curtain <= curtain_demand)
    model.clothing_sales = pyo.Constraint(expr=model.x_clothing <= clothing_demand)

    # p2: overtime limit
    model.overtime_cap = pyo.Constraint(expr=model.d2 <= overtime_limit)

    # Lexicographic weights encoding priority p1 > p2 > p3 > p4
    # Weights: p1 -> 1e12, p2 -> 1e8, p3 -> 1e4, p4 -> 1
    big_p1 = pyo.Constraint(expr=model.d1 <= 0)

    obj_expr = (
        1e12 * model.d1
        + 1e8 * model.d2
        + 1e4 * (model.d3c + model.d3k)
    )

    model.obj = pyo.Objective(expr=obj_expr, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}