import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producers = [0, 1, 2]
    contracts = [0, 1, 2, 3]

    capacity = {
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
    min_delivery = {
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

    model.producers = pyo.Set(initialize=producers)
    model.contracts = pyo.Set(initialize=contracts)
    model.links = pyo.Set(initialize=[(p, c) for p in producers for c in contracts], dimen=2)

    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.links, domain=pyo.Binary)

    def x_upper(mdl, p, c):
        return mdl.x[p, c] <= capacity[p] * mdl.y[p, c]
    model.x_upper = pyo.Constraint(model.links, rule=x_upper)

    def x_lower(mdl, p, c):
        return mdl.x[p, c] >= min_delivery[p] * mdl.y[p, c]
    model.x_lower = pyo.Constraint(model.links, rule=x_lower)

    def cap_rule(mdl, p):
        return sum(mdl.x[p, c] for c in contracts) <= capacity[p]
    model.cap = pyo.Constraint(model.producers, rule=cap_rule)

    def demand_rule(mdl, c):
        return sum(mdl.x[p, c] for p in producers) >= demand[c]
    model.dem = pyo.Constraint(model.contracts, rule=demand_rule)

    def two_producers_rule(mdl, c):
        return sum(mdl.y[p, c] for p in producers) >= 2
    model.two_producers = pyo.Constraint(model.contracts, rule=two_producers_rule)

    def obj_rule(mdl):
        return sum(cost[(p, c)] * mdl.x[p, c] for p in producers for c in contracts)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": obj_val, "status": "optimal"}