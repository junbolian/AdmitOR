import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = range(n_orig)
    dests = range(n_dest)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, dests, within=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in dests) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)
    model.demand_con = pyo.Constraint(dests, rule=demand_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in origins for j in dests),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}