# IR: {"sets":{"P":[0,1,2,3,4,5,6,7,8,9,10],"L":[0,1,2,3,4],"uses":{"0":[1,2,4,5,6,7],"1":[0,2,4,6,8,9,10],"2":[2,3,4,10],"3":[1,6,7,10],"4":[1,3,6,7,8,9]}},"params":{"revenue":"P-indexed","demand_limit":"P-indexed","flight_capacity":"L-indexed"},"variables":{"sold[p]":"nonnegative integer, p in P"},"constraints":["sold[p] <= demand_limit[p] for p in P","sum(sold[p] for p in uses[l]) <= flight_capacity[l] for l in L"],"objective":"maximize sum(revenue[p] * sold[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    flight_capacity = params["flight_capacity"]

    uses = {
        0: (1, 2, 4, 5, 6, 7),
        1: (0, 2, 4, 6, 8, 9, 10),
        2: (2, 3, 4, 10),
        3: (1, 6, 7, 10),
        4: (1, 3, 6, 7, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 10)
    model.L = pyo.RangeSet(0, 4)

    model.revenue = pyo.Param(
        model.P, initialize={p: revenue[p] for p in model.P}
    )
    model.demand_limit = pyo.Param(
        model.P, initialize={p: demand_limit[p] for p in model.P}
    )
    model.flight_capacity = pyo.Param(
        model.L, initialize={leg: flight_capacity[leg] for leg in model.L}
    )

    model.sold = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(model, p):
        return model.sold[p] <= model.demand_limit[p]

    model.demand_constraints = pyo.Constraint(model.P, rule=demand_rule)

    def capacity_rule(model, leg):
        return (
            sum(model.sold[p] for p in uses[leg])
            <= model.flight_capacity[leg]
        )

    model.capacity_constraints = pyo.Constraint(model.L, rule=capacity_rule)

    model.total_revenue = pyo.Objective(
        expr=sum(model.revenue[p] * model.sold[p] for p in model.P),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}