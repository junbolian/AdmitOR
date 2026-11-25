import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()
    model.orig = pyo.RangeSet(0, n_orig - 1)
    model.dest = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.orig, model.dest, domain=pyo.NonNegativeReals)

    def cost_rule(mdl):
        return sum(
            transport_cost[i][j] * mdl.x[i, j]
            for i in mdl.orig
            for j in mdl.dest
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.dest) == supply[i]

    model.supply_con = pyo.Constraint(model.orig, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.orig) == demand[j]

    model.demand_con = pyo.Constraint(model.dest, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}