import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = list(range(n_orig))
    dests = list(range(n_dest))

    model = pyo.ConcreteModel()
    model.i = pyo.Set(initialize=origins)
    model.j = pyo.Set(initialize=dests)

    model.x = pyo.Var(model.i, model.j, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.j) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.i) == demand[j]

    model.supply_con = pyo.Constraint(model.i, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.j, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.i for j in mdl.j)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}