import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.trucks_A = pyo.Var(domain=pyo.NonNegativeReals)
    model.trucks_B = pyo.Var(domain=pyo.NonNegativeReals)

    model.demand_A_con = pyo.Constraint(
        expr=params["supply_A_per_truck"] * model.trucks_A
        + params["supply_A_per_truck_B"] * model.trucks_B
        >= params["demand_A"]
    )
    model.demand_B_con = pyo.Constraint(
        expr=params["supply_B_per_truck"] * model.trucks_A
        + params["supply_B_per_truck_B"] * model.trucks_B
        >= params["demand_B"]
    )
    model.demand_C_con = pyo.Constraint(
        expr=params["supply_C_per_truck_A"] * model.trucks_A
        + params["supply_C_per_truck_B"] * model.trucks_B
        >= params["demand_C"]
    )

    model.total_cost = pyo.Objective(
        expr=params["cost_per_truck_A"] * model.trucks_A
        + params["cost_per_truck_B"] * model.trucks_B,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}