import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 5
    periods = list(range(T))

    fixed_setup_cost = params["fixed_setup_cost"]
    variable_production_cost = params["variable_production_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    backlog_penalty = params["backlog_penalty"]
    production_capacity = params["production_capacity"]
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.back = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.T, domain=pyo.Binary)

    model.prod_cap = pyo.Constraint(
        model.T,
        rule=lambda m, t: m.prod[t] <= production_capacity * m.setup[t],
    )

    def balance_rule(m, t):
        prev_inv = 0 if t == 0 else m.inv[t - 1]
        prev_back = 0 if t == 0 else m.back[t - 1]
        return m.prod[t] + prev_inv - prev_back == demand[t] + m.inv[t] - m.back[t]

    model.balance = pyo.Constraint(model.T, rule=balance_rule)

    model.final_inv = pyo.Constraint(expr=model.inv[T - 1] == 0)
    model.final_back = pyo.Constraint(expr=model.back[T - 1] == 0)

    def cost_rule(m):
        return sum(
            fixed_setup_cost[t] * m.setup[t]
            + variable_production_cost[t] * m.prod[t]
            + inventory_holding_cost[t] * m.inv[t]
            + backlog_penalty[t] * m.back[t]
            for t in m.T
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}