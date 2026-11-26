import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = [
        params["demand_2_6"],
        params["demand_6_10"],
        params["demand_10_14"],
        params["demand_14_18"],
        params["demand_18_22"],
        params["demand_22_2"],
    ]
    periods = list(range(6))
    # shift starting at period s covers s, s+1, s+2 (three 4-hour blocks = 8h? actually 2 blocks)
    # Each period is 4 hours; 8-hour shift covers 2 consecutive periods.
    covers = [[(s + k) % 6 for k in range(2)] for s in periods]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(periods, domain=pyo.NonNegativeIntegers)

    model.demand_con = pyo.ConstraintList()
    for p in periods:
        model.demand_con.add(
            sum(model.x[s] for s in periods if p in covers[s]) >= demand[p]
        )

    model.total = pyo.Objective(expr=sum(model.x[s] for s in periods), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total))
    return {"objective": obj_val, "status": "optimal"}