import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    pollution_cap = params["pollution_cap"]
    min_truck_trips = params["min_truck_trips"]
    capacity_truck = params["capacity_truck"]
    capacity_van = params["capacity_van"]
    capacity_motorcycle = params["capacity_motorcycle"]
    capacity_ev = params["capacity_ev"]
    pollution_truck = params["pollution_truck"]
    pollution_van = params["pollution_van"]
    pollution_motorcycle = params["pollution_motorcycle"]
    pollution_ev = params["pollution_ev"]

    model = pyo.ConcreteModel()

    model.T = pyo.Var(domain=pyo.NonNegativeReals)
    model.V = pyo.Var(domain=pyo.NonNegativeReals)
    model.M = pyo.Var(domain=pyo.NonNegativeReals)
    model.E = pyo.Var(domain=pyo.NonNegativeReals)

    # binary choice: van vs ev
    model.zV = pyo.Var(domain=pyo.Binary)
    model.zE = pyo.Var(domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=pollution_truck * model.T
        + pollution_van * model.V
        + pollution_motorcycle * model.M
        + pollution_ev * model.E,
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        expr=capacity_truck * model.T
        + capacity_van * model.V
        + capacity_motorcycle * model.M
        + capacity_ev * model.E
        >= demand
    )

    model.pollution_con = pyo.Constraint(
        expr=pollution_truck * model.T
        + pollution_van * model.V
        + pollution_motorcycle * model.M
        + pollution_ev * model.E
        <= pollution_cap
    )

    model.truck_con = pyo.Constraint(expr=model.T >= min_truck_trips)

    # van and ev mutually exclusive
    model.choice_con = pyo.Constraint(expr=model.zV + model.zE <= 1)

    bigM = demand + pollution_cap + 1000
    model.van_ub = pyo.Constraint(expr=model.V <= bigM * model.zV)
    model.ev_ub = pyo.Constraint(expr=model.E <= bigM * model.zE)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}