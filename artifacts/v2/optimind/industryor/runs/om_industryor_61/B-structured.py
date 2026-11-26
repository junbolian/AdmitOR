# IR: {"sets":{"modes":["horse","bicycle","handcart"]},"params":["demand","pollution_horse","pollution_bicycle","pollution_handcart","pollution_budget","min_horse_trips","capacity_horse","capacity_bicycle","capacity_handcart"],"derived":{"U_bicycle":"max(1,ceil(demand/capacity_bicycle))","U_handcart":"max(1,ceil(demand/capacity_handcart))"},"variables":{"horse_trips":"NonNegativeIntegers","bicycle_trips":"NonNegativeIntegers","handcart_trips":"NonNegativeIntegers","choose_bicycle":"Binary"},"constraints":["capacity_horse*horse_trips + capacity_bicycle*bicycle_trips + capacity_handcart*handcart_trips >= demand","pollution_horse*horse_trips + pollution_bicycle*bicycle_trips + pollution_handcart*handcart_trips <= pollution_budget","horse_trips >= min_horse_trips","bicycle_trips <= U_bicycle*choose_bicycle","handcart_trips <= U_handcart*(1-choose_bicycle)","bicycle_trips >= choose_bicycle","handcart_trips >= 1-choose_bicycle"],"objective":"minimize pollution_horse*horse_trips + pollution_bicycle*bicycle_trips + pollution_handcart*handcart_trips"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = float(params["demand"])
    pollution_horse = float(params["pollution_horse"])
    pollution_bicycle = float(params["pollution_bicycle"])
    pollution_handcart = float(params["pollution_handcart"])
    pollution_budget = float(params["pollution_budget"])
    min_horse_trips = float(params["min_horse_trips"])
    capacity_horse = float(params["capacity_horse"])
    capacity_bicycle = float(params["capacity_bicycle"])
    capacity_handcart = float(params["capacity_handcart"])

    numeric_values = (
        demand,
        pollution_horse,
        pollution_bicycle,
        pollution_handcart,
        pollution_budget,
        min_horse_trips,
        capacity_horse,
        capacity_bicycle,
        capacity_handcart,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        return {"objective": None, "status": "invalid_parameters"}

    if (
        demand < 0
        or min_horse_trips < 0
        or min(capacity_horse, capacity_bicycle, capacity_handcart) <= 0
        or min(pollution_horse, pollution_bicycle, pollution_handcart) < 0
    ):
        return {"objective": None, "status": "invalid_parameters"}

    # These finite trip caps preserve an optimum: either selected mode
    # can satisfy demand by itself at its cap, and additional trips
    # cannot improve feasibility or reduce nonnegative pollution.
    upper_bicycle = max(1, math.ceil(demand / capacity_bicycle))
    upper_handcart = max(1, math.ceil(demand / capacity_handcart))

    model = pyo.ConcreteModel()

    model.horse_trips = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.bicycle_trips = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.handcart_trips = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.choose_bicycle = pyo.Var(domain=pyo.Binary)

    model.produce_requirement = pyo.Constraint(
        expr=(
            capacity_horse * model.horse_trips
            + capacity_bicycle * model.bicycle_trips
            + capacity_handcart * model.handcart_trips
            >= demand
        )
    )

    pollution_expression = (
        pollution_horse * model.horse_trips
        + pollution_bicycle * model.bicycle_trips
        + pollution_handcart * model.handcart_trips
    )

    model.pollution_limit = pyo.Constraint(
        expr=pollution_expression <= pollution_budget
    )
    model.horse_requirement = pyo.Constraint(
        expr=model.horse_trips >= min_horse_trips
    )
    model.bicycle_selection_upper = pyo.Constraint(
        expr=model.bicycle_trips <= upper_bicycle * model.choose_bicycle
    )
    model.handcart_selection_upper = pyo.Constraint(
        expr=model.handcart_trips <= upper_handcart * (1 - model.choose_bicycle)
    )
    model.bicycle_selection_lower = pyo.Constraint(
        expr=model.bicycle_trips >= model.choose_bicycle
    )
    model.handcart_selection_lower = pyo.Constraint(
        expr=model.handcart_trips >= 1 - model.choose_bicycle
    )

    model.total_pollution = pyo.Objective(
        expr=pollution_expression,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_pollution))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}