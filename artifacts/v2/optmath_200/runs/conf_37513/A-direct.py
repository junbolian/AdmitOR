import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    planes = [0, 1]
    locs = [0, 1]

    def plane_capacity(p):
        return params["capacity_p0"] if p == 0 else params["capacity_p1"]

    def cost(p, i, j):
        if i == j:
            return 0.0
        key = "cost_p{}_{}_{}".format(p, i, j)
        return params[key]

    model = pyo.ConcreteModel()

    # Deployed planes x[p, i, j]
    model.x = pyo.Var(planes, locs, locs, domain=pyo.NonNegativeIntegers)

    # Idle planes at start of period I[p, i]
    model.I = pyo.Var(planes, locs, domain=pyo.NonNegativeIntegers)

    # Objective: minimize deployment cost
    def obj_rule(md):
        return sum(cost(p, i, j) * md.x[p, i, j]
                   for p in planes for i in locs for j in locs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Initial idle balance:
    # initial_idle[p,i] = I[p,i] + sum_j x[p,i,j]
    # where initial_idle[p,i] is the total planes at location i.
    # Represent initial_idle as a variable too.
    model.init_idle = pyo.Var(planes, locs, domain=pyo.NonNegativeIntegers)

    def init_balance_rule(md, p, i):
        return md.init_idle[p, i] == md.I[p, i] + sum(md.x[p, i, j] for j in locs)
    model.init_balance = pyo.Constraint(planes, locs, rule=init_balance_rule)

    # Availability: sum_i I[p,i] <= avail_p
    def avail_rule(md, p):
        if p == 0:
            return sum(md.I[p, i] for i in locs) <= params["avail_p0"]
        else:
            return sum(md.I[p, i] for i in locs) <= params["avail_p1"]
    model.avail = pyo.Constraint(planes, rule=avail_rule)

    # Demand on route 1->0: capacity sum >= demand
    def demand_rule(md):
        return (plane_capacity(0) * md.x[0, 1, 0] +
                plane_capacity(1) * md.x[1, 1, 0]) >= params["demand_1_0"]
    model.demand = pyo.Constraint(rule=demand_rule)

    # No deployment 0->1
    def forbid_rule(md, p):
        return md.x[p, 0, 1] == 0
    model.forbid_01 = pyo.Constraint(planes, rule=forbid_rule)

    # Max deploy 1->0 per type
    def max_deploy_rule(md, p):
        return md.x[p, 1, 0] <= params["max_deploy_1_0"]
    model.max_deploy_10 = pyo.Constraint(planes, rule=max_deploy_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}