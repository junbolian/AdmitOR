import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Read parameters
    moto_poll = params["motorcycle_pollution"]
    small_poll = params["small_truck_pollution"]
    large_poll = params["large_truck_pollution"]
    moto_prod = params["motorcycle_product"]
    small_prod = params["small_truck_product"]
    large_prod = params["large_truck_product"]
    moto_max = params["motorcycle_max_trips"]
    demand = params["product_demand"]
    max_trips = params["max_total_trips"]

    # Modes: 0 = motorcycle, 1 = small truck, 2 = large truck
    modes = [0, 1, 2]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(modes, domain=pyo.NonNegativeIntegers)
    model.z = pyo.Var(modes, domain=pyo.Binary)

    # Objective: minimize total pollution
    model.obj = pyo.Objective(
        expr=(
            moto_poll * model.x[0]
            + small_poll * model.x[1]
            + large_poll * model.x[2]
        ),
        sense=pyo.minimize,
    )

    # Demand constraint
    model.demand_con = pyo.Constraint(
        expr=(
            moto_prod * model.x[0]
            + small_prod * model.x[1]
            + large_prod * model.x[2]
            >= demand
        )
    )

    # Total trips constraint
    model.total_trips_con = pyo.Constraint(
        expr=model.x[0] + model.x[1] + model.x[2] <= max_trips
    )

    # Motorcycle trip limit
    model.moto_max_con = pyo.Constraint(expr=model.x[0] <= moto_max)

    # Exactly two modes chosen
    model.two_modes_con = pyo.Constraint(
        expr=model.z[0] + model.z[1] + model.z[2] == 2
    )

    # Link binary selection with usage: x[i] <= bigM * z[i]
    big_m = max_trips + moto_max
    model.link_con = pyo.Constraint(
        modes, rule=lambda m, i: m.x[i] <= big_m * m.z[i]
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}