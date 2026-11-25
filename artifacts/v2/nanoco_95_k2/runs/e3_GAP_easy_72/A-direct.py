import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_orders = 7
    n_dcs = 3
    dcs = range(n_dcs)
    orders = range(n_orders)

    capacity = {
        0: params["capacity_DC1"],
        1: params["capacity_DC2"],
        2: params["capacity_DC3"],
    }
    storage = {
        0: [params["storage_DC1"][i] for i in orders],
        1: [params["storage_DC2"][i] for i in orders],
        2: [params["storage_DC3"][i] for i in orders],
    }
    cost = {
        0: [params["cost_DC1"][i] for i in orders],
        1: [params["cost_DC2"][i] for i in orders],
        2: [params["cost_DC3"][i] for i in orders],
    }

    model = pyo.ConcreteModel()
    model.DCS = pyo.Set(initialize=list(dcs))
    model.ORDERS = pyo.Set(initialize=list(orders))
    model.x = pyo.Var(model.DCS, model.ORDERS, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[d][o] * mdl.x[d, o] for d in mdl.DCS for o in mdl.ORDERS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(mdl, o):
        return sum(mdl.x[d, o] for d in mdl.DCS) == 1
    model.assign_con = pyo.Constraint(model.ORDERS, rule=assign_rule)

    def cap_rule(mdl, d):
        return sum(storage[d][o] * mdl.x[d, o] for o in mdl.ORDERS) <= capacity[d]
    model.cap_con = pyo.Constraint(model.DCS, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}