import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = int(params["period_count"])
    prod_cost = params["production_cost"]
    hold_cost = params["holding_cost"]
    back_cost = params["backlog_cost"]
    setup_cost = params["setup_cost"]
    cap = params["production_capacity"]
    demand = params["demand"]

    periods = list(range(T))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, within=pyo.Binary)
    model.inv = pyo.Var(model.P, within=pyo.NonNegativeReals)
    model.back = pyo.Var(model.P, within=pyo.NonNegativeReals)

    # Inventory/backlog balance: inv[t] - back[t] = inv[t-1] - back[t-1] + x[t] - d[t]
    def balance_rule(mdl, t):
        prev_inv = mdl.inv[t - 1] if t - 1 in mdl.P else 0.0
        prev_back = mdl.back[t - 1] if t - 1 in mdl.P else 0.0
        return mdl.inv[t] - mdl.back[t] == prev_inv - prev_back + mdl.x[t] - demand[t]
    model.balance = pyo.Constraint(model.P, rule=balance_rule)

    # Capacity linking
    def cap_rule(mdl, t):
        return mdl.x[t] <= cap * mdl.y[t]
    model.capacity = pyo.Constraint(model.P, rule=cap_rule)

    # Zero ending inventory and backlog
    def end_inv_rule(mdl):
        return mdl.inv[T - 1] == 0
    model.end_inv = pyo.Constraint(rule=end_inv_rule)

    def end_back_rule(mdl):
        return mdl.back[T - 1] == 0
    model.end_back = pyo.Constraint(rule=end_back_rule)

    def obj_rule(mdl):
        return sum(
            prod_cost[t] * mdl.x[t]
            + hold_cost[t] * mdl.inv[t]
            + back_cost[t] * mdl.back[t]
            + setup_cost[t] * mdl.y[t]
            for t in mdl.P
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}