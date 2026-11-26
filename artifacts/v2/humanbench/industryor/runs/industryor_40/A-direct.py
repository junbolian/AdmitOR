import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: number of trips per vehicle type
    model.x_truck = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_van = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_motorcycle = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_ev = pyo.Var(domain=pyo.NonNegativeReals)

    # Binary selection between van and EV (choose at most one)
    model.y_van = pyo.Var(domain=pyo.Binary)
    model.y_ev = pyo.Var(domain=pyo.Binary)

    # Demand constraint
    model.demand_con = pyo.Constraint(
        expr=params["truck_capacity"] * model.x_truck
        + params["van_capacity"] * model.x_van
        + params["motorcycle_capacity"] * model.x_motorcycle
        + params["ev_capacity"] * model.x_ev
        >= params["demand_required"]
    )

    # Pollution budget constraint
    model.pollution_con = pyo.Constraint(
        expr=params["truck_pollution"] * model.x_truck
        + params["van_pollution"] * model.x_van
        + params["motorcycle_pollution"] * model.x_motorcycle
        + params["ev_pollution"] * model.x_ev
        <= params["pollution_budget"]
    )

    # Minimum truck trips
    model.truck_min_con = pyo.Constraint(
        expr=model.x_truck >= params["truck_min_trips"]
    )

    # Big-M linking for van/EV exclusivity
    big_m = max(
        params["demand_required"] / params["van_capacity"],
        params["demand_required"] / params["ev_capacity"],
    ) + params["demand_required"]

    model.van_link = pyo.Constraint(
        expr=model.x_van <= big_m * model.y_van
    )
    model.ev_link = pyo.Constraint(
        expr=model.x_ev <= big_m * model.y_ev
    )
    model.choose_one = pyo.Constraint(
        expr=model.y_van + model.y_ev <= 1
    )

    # Objective: minimize total pollution
    model.total_pollution = pyo.Expression(
        expr=params["truck_pollution"] * model.x_truck
        + params["van_pollution"] * model.x_van
        + params["motorcycle_pollution"] * model.x_motorcycle
        + params["ev_pollution"] * model.x_ev
    )

    model.obj = pyo.Objective(expr=model.total_pollution, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}