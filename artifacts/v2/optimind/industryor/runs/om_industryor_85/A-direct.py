import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    ref_cap_A = params["refrigerated_capacity_A"]
    nonref_cap_A = params["nonrefrigerated_capacity_A"]
    total_cap_B = params["total_capacity_B"]
    ref_demand = params["refrigerated_demand"]
    nonref_demand = params["nonrefrigerated_demand"]
    cost_A = params["cost_per_km_A"]
    cost_B = params["cost_per_km_B"]

    # Type B splits total capacity equally between refrigerated and non-refrigerated
    ref_cap_B = total_cap_B / 2.0
    nonref_cap_B = total_cap_B / 2.0

    model = pyo.ConcreteModel()
    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.ref_constraint = pyo.Constraint(
        expr=ref_cap_A * model.xA + ref_cap_B * model.xB >= ref_demand
    )
    model.nonref_constraint = pyo.Constraint(
        expr=nonref_cap_A * model.xA + nonref_cap_B * model.xB >= nonref_demand
    )

    model.total_cost = pyo.Objective(
        expr=cost_A * model.xA + cost_B * model.xB, sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}