import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = list(range(n_orig))
    dests = list(range(n_dest))
    pairs = [(i, j) for i in origins for j in dests]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def rule_supply(mdl, i):
        return sum(mdl.x[i, j] for j in dests) == supply[i]
    model.con_supply = pyo.Constraint(origins, rule=rule_supply)

    def rule_demand(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]
    model.con_demand = pyo.Constraint(dests, rule=rule_demand)

    model.cost = pyo.Objective(
        expr=sum(transport_cost[i][j] * model.x[i, j] for (i, j) in pairs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}