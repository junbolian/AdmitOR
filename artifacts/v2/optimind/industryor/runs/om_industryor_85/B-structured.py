# IR: {"sets":{"truck_types":["A","B"],"cargo_types":["refrigerated","nonrefrigerated"]},"params":["refrigerated_capacity_A","nonrefrigerated_capacity_A","total_capacity_B","refrigerated_demand","nonrefrigerated_demand","cost_per_km_A","cost_per_km_B"],"variables":{"trucks_A":"nonnegative integer","trucks_B":"nonnegative integer"},"constraints":["refrigerated_capacity_A*trucks_A+(total_capacity_B/2)*trucks_B>=refrigerated_demand","nonrefrigerated_capacity_A*trucks_A+(total_capacity_B/2)*trucks_B>=nonrefrigerated_demand"],"objective":"minimize cost_per_km_A*trucks_A+cost_per_km_B*trucks_B"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    refrigerated_capacity_A = params["refrigerated_capacity_A"]
    nonrefrigerated_capacity_A = params["nonrefrigerated_capacity_A"]
    total_capacity_B = params["total_capacity_B"]
    refrigerated_demand = params["refrigerated_demand"]
    nonrefrigerated_demand = params["nonrefrigerated_demand"]
    cost_per_km_A = params["cost_per_km_A"]
    cost_per_km_B = params["cost_per_km_B"]

    model = pyo.ConcreteModel()

    model.trucks_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.trucks_B = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.refrigerated_requirement = pyo.Constraint(
        expr=(
            refrigerated_capacity_A * model.trucks_A
            + (total_capacity_B / 2) * model.trucks_B
            >= refrigerated_demand
        )
    )
    model.nonrefrigerated_requirement = pyo.Constraint(
        expr=(
            nonrefrigerated_capacity_A * model.trucks_A
            + (total_capacity_B / 2) * model.trucks_B
            >= nonrefrigerated_demand
        )
    )

    model.total_cost = pyo.Objective(
        expr=(
            cost_per_km_A * model.trucks_A
            + cost_per_km_B * model.trucks_B
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}