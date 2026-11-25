import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_dests = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.dests = pyo.RangeSet(0, n_dests - 1)

    model.x = pyo.Var(model.origins, model.dests, domain=pyo.NonNegativeReals)

    def ship_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.dests) == supply[i]

    model.ship = pyo.Constraint(model.origins, rule=ship_rule)

    def recv_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.origins) == demand[j]

    model.recv = pyo.Constraint(model.dests, rule=recv_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.cap = pyo.Constraint(model.origins, model.dests, rule=cap_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j]
                   for i in mdl.origins for j in mdl.dests)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}