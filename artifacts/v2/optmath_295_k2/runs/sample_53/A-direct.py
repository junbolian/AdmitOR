import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.ORIG = pyo.RangeSet(0, n_orig - 1)
    model.DEST = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.ORIG, model.DEST, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.DEST) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.ORIG) == demand[j]

    model.supply_con = pyo.Constraint(model.ORIG, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.DEST, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.ORIG for j in mdl.DEST)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}