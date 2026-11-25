import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    latency = params["latency"]

    num_users = len(latency)
    num_locs = len(fixed_cost)

    model = pyo.ConcreteModel()
    model.users = pyo.RangeSet(0, num_users - 1)
    model.locs = pyo.RangeSet(0, num_locs - 1)

    model.y = pyo.Var(model.locs, domain=pyo.Binary)
    model.x = pyo.Var(model.users, model.locs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(fixed_cost[j] * mdl.y[j] for j in mdl.locs) + \
               sum(latency[i][j] * mdl.x[i, j] for i in mdl.users for j in mdl.locs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.locs) == 1

    model.assign = pyo.Constraint(model.users, rule=assign_rule)

    def link_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.y[j]

    model.link = pyo.Constraint(model.users, model.locs, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}