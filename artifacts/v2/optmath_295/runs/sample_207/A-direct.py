import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    weeks = list(range(7))
    products = ['A', 'B']

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=weeks)
    model.P = pyo.Set(initialize=products)

    demand = {'A': params["demand_A"], 'B': params["demand_B"]}
    prod_cost = {'A': params["prod_cost_A"], 'B': params["prod_cost_B"]}
    setup_cost = {'A': params["setup_cost_A"], 'B': params["setup_cost_B"]}
    hold_cost = {'A': params["hold_cost_A"], 'B': params["hold_cost_B"]}
    maxq = {'A': params["limit_A"], 'B': params["limit_B"]}
    res_use = {'A': params["resource_A"], 'B': params["resource_B"]}
    capacity = params["capacity"]

    model.x = pyo.Var(model.P, model.W, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.W, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.W, domain=pyo.Binary)

    def balance_rule(model, p, t):
        prev = 0 if t == 0 else model.inv[p, t - 1]
        return model.inv[p, t] == prev + model.x[p, t] - demand[p][t]

    model.balance = pyo.Constraint(model.P, model.W, rule=balance_rule)

    def cap_rule(model, t):
        return sum(res_use[p] * model.x[p, t] for p in model.P) <= capacity[t]

    model.cap = pyo.Constraint(model.W, rule=cap_rule)

    def setup_rule(model, p, t):
        return model.x[p, t] <= maxq[p][t] * model.y[p, t]

    model.setup = pyo.Constraint(model.P, model.W, rule=setup_rule)

    def obj_rule(model):
        return (
            sum(prod_cost[p][t] * model.x[p, t] for p in model.P for t in model.W)
            + sum(setup_cost[p][t] * model.y[p, t] for p in model.P for t in model.W)
            + sum(hold_cost[p][t] * model.inv[p, t] for p in model.P for t in model.W)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}