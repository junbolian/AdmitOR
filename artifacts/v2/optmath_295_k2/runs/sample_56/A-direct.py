import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producers = [0, 1, 2]
    contracts = [0, 1, 2, 3]

    cap = {
        0: params["capacity_P0"],
        1: params["capacity_P1"],
        2: params["capacity_P2"],
    }
    demand = {
        0: params["demand_C0"],
        1: params["demand_C1"],
        2: params["demand_C2"],
        3: params["demand_C3"],
    }
    min_del = {
        0: params["min_delivery_P0"],
        1: params["min_delivery_P1"],
        2: params["min_delivery_P2"],
    }
    cost = {
        (0, 0): params["cost_P0_C0"],
        (0, 1): params["cost_P0_C1"],
        (0, 2): params["cost_P0_C2"],
        (0, 3): params["cost_P0_C3"],
        (1, 0): params["cost_P1_C0"],
        (1, 1): params["cost_P1_C1"],
        (1, 2): params["cost_P1_C2"],
        (1, 3): params["cost_P1_C3"],
        (2, 0): params["cost_P2_C0"],
        (2, 1): params["cost_P2_C1"],
        (2, 2): params["cost_P2_C2"],
        (2, 3): params["cost_P2_C3"],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)
    model.PC = pyo.Set(initialize=[(p, c) for p in producers for c in contracts])

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(p, c)] * m.x[p, c] for p in producers for c in contracts)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, p):
        return sum(m.x[p, c] for c in contracts) <= cap[p]

    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in producers) >= demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def prov_count_rule(m, c):
        return sum(m.y[p, c] for p in producers) >= 2

    model.prov_count_con = pyo.Constraint(model.C, rule=prov_count_rule)

    def min_lb_rule(m, p, c):
        return m.x[p, c] >= min_del[p] * m.y[p, c]

    model.min_lb_con = pyo.Constraint(model.PC, rule=min_lb_rule)

    def max_ub_rule(m, p, c):
        return m.x[p, c] <= cap[p] * m.y[p, c]

    model.max_ub_con = pyo.Constraint(model.PC, rule=max_ub_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}