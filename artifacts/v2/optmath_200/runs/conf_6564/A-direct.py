import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.ORIG = pyo.RangeSet(0, n_orig - 1)
    model.DEST = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.ORIG, model.DEST, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j]
                   for i in range(n_orig) for j in range(n_dest))
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in range(n_dest)) == supply[i]
    model.supply_con = pyo.Constraint(model.ORIG, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in range(n_orig)) == demand[j]
    model.demand_con = pyo.Constraint(model.DEST, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]
    model.cap_con = pyo.Constraint(model.ORIG, model.DEST, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}