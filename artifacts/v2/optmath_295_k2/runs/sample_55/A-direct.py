import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.orig = pyo.RangeSet(0, n_orig - 1)
    model.dest = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.orig, model.dest, domain=pyo.NonNegativeReals)

    def supply_rule(md, i):
        return sum(md.x[i, j] for j in md.dest) == supply[i]

    def demand_rule(md, j):
        return sum(md.x[i, j] for i in md.orig) == demand[j]

    model.supply_con = pyo.Constraint(model.orig, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.dest, rule=demand_rule)

    def obj_rule(md):
        return sum(cost[i][j] * md.x[i, j] for i in md.orig for j in md.dest)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}