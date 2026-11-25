import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_wh = 5
    n_st = 6
    warehouses = list(range(n_wh))
    stores = list(range(n_st))

    supply = {
        0: list(params["supply_product0"]),
        1: list(params["supply_product1"]),
    }
    demand = {
        0: list(params["demand_product0"]),
        1: list(params["demand_product1"]),
    }
    tcost = {
        0: [list(row) for row in params["transport_cost_product0"]],
        1: [list(row) for row in params["transport_cost_product1"]],
    }
    cap = [list(row) for row in params["link_capacity"]]

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses)
    model.S = pyo.Set(initialize=stores)
    model.P = pyo.Set(initialize=[0, 1])

    model.x = pyo.Var(model.W, model.S, model.P, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(
            tcost[p][w][s] * m.x[w, s, p]
            for w in m.W for s in m.S for p in m.P
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(m, w, p):
        return sum(m.x[w, s, p] for s in m.S) <= supply[p][w]

    model.supply_con = pyo.Constraint(model.W, model.P, rule=supply_rule)

    def demand_rule(m, s, p):
        return sum(m.x[w, s, p] for w in m.W) == demand[p][s]

    model.demand_con = pyo.Constraint(model.S, model.P, rule=demand_rule)

    def cap_rule(m, w, s):
        return sum(m.x[w, s, p] for p in m.P) <= cap[w][s]

    model.cap_con = pyo.Constraint(model.W, model.S, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}