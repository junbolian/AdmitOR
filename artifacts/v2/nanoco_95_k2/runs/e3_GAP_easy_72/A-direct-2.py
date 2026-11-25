import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    orders = list(range(7))
    dcs = [1, 2, 3]

    capacity = {
        1: params["capacity_DC1"],
        2: params["capacity_DC2"],
        3: params["capacity_DC3"],
    }
    storage = {
        1: [params["storage_DC1"][i] for i in orders],
        2: [params["storage_DC2"][i] for i in orders],
        3: [params["storage_DC3"][i] for i in orders],
    }
    cost = {
        1: [params["cost_DC1"][i] for i in orders],
        2: [params["cost_DC2"][i] for i in orders],
        3: [params["cost_DC3"][i] for i in orders],
    }

    model = pyo.ConcreteModel()
    model.orders = pyo.Set(initialize=orders, dimen=1)
    model.dcs = pyo.Set(initialize=dcs, dimen=1)
    model.x = pyo.Var(model.orders, model.dcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            cost[d][i] * m.x[i, d]
            for i in orders
            for d in dcs
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, d] for d in dcs) == 1

    model.assign_eq = pyo.Constraint(model.orders, rule=assign_rule)

    def cap_rule(m, d):
        return sum(storage[d][i] * m.x[i, d] for i in orders) <= capacity[d]

    model.cap_con = pyo.Constraint(model.dcs, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}