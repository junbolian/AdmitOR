import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    resource_usage = params["resource_usage"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    products = list(range(3))
    weeks = list(range(8))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.W = pyo.Set(initialize=weeks)

    model.prod = pyo.Var(model.P, model.W, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.W, within=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.P, model.W, within=pyo.Binary)

    def obj_rule(m):
        return (
            sum(production_cost[p][w] * m.prod[p, w] for p in m.P for w in m.W)
            + sum(setup_cost[p][w] * m.setup[p, w] for p in m.P for w in m.W)
            + sum(holding_cost * m.inv[p, w] for p in m.P for w in m.W)
        )
    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, p, w):
        prev_inv = m.inv[p, w - 1] if w > 0 else 0
        return prev_inv + m.prod[p, w] - m.inv[p, w] == demand[p][w]
    model.balance = pyo.Constraint(model.P, model.W, rule=balance_rule)

    def resource_rule(m, w):
        return sum(resource_usage[p] * m.prod[p, w] for p in m.P) <= resource_capacity[w]
    model.resource = pyo.Constraint(model.W, rule=resource_rule)

    def bigm_rule(m, p, w):
        return m.prod[p, w] <= production_limit[p][w] * m.setup[p, w]
    model.bigm = pyo.Constraint(model.P, model.W, rule=bigm_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}
    return {"objective": obj_val, "status": "optimal"}