import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    pollution_budget = params["pollution_budget"]
    pollution_per_horse_trip = params["pollution_per_horse_trip"]
    pollution_per_bicycle_trip = params["pollution_per_bicycle_trip"]
    pollution_per_handcart_trip = params["pollution_per_handcart_trip"]
    min_horse_trips = params["min_horse_trips"]
    capacity_horse = params["capacity_horse"]
    capacity_bicycle = params["capacity_bicycle"]
    capacity_handcart = params["capacity_handcart"]

    model = pyo.ConcreteModel()

    model.horse_trips = pyo.Var(domain=pyo.NonNegativeReals)
    model.bicycle_trips = pyo.Var(domain=pyo.NonNegativeReals)
    model.handcart_trips = pyo.Var(domain=pyo.NonNegativeReals)
    model.choose_bicycle = pyo.Var(domain=pyo.Binary)

    model.min_horse = pyo.Constraint(expr=model.horse_trips >= min_horse_trips)

    model.demand_con = pyo.Constraint(
        expr=capacity_horse * model.horse_trips
        + capacity_bicycle * model.bicycle_trips
        + capacity_handcart * model.handcart_trips
        >= demand
    )

    model.pollution_con = pyo.Constraint(
        expr=pollution_per_horse_trip * model.horse_trips
        + pollution_per_bicycle_trip * model.bicycle_trips
        + pollution_per_handcart_trip * model.handcart_trips
        <= pollution_budget
    )

    big_m = demand
    model.bicycle_link = pyo.Constraint(
        expr=model.bicycle_trips <= big_m * model.choose_bicycle
    )
    model.handcart_link = pyo.Constraint(
        expr=model.handcart_trips <= big_m * (1 - model.choose_bicycle)
    )

    model.total_trips = pyo.Objective(
        expr=model.horse_trips + model.bicycle_trips + model.handcart_trips,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_trips))
    return {"objective": obj_val, "status": "optimal"}