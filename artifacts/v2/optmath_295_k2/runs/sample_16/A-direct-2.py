import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    arc_capacity = params["arc_capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.O = pyo.RangeSet(0, n_orig - 1)
    model.D = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.O, model.D, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.D) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.O) == demand[j]

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= arc_capacity[i][j]

    model.supply_con = pyo.Constraint(model.O, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.D, rule=demand_rule)
    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.O for j in model.D),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}