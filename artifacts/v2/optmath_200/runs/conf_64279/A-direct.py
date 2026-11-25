import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    fixed_order_cost = params["fixed_order_cost"]
    holding_cost = params["holding_cost"]
    backlog_cost = params["backlog_cost"]
    demand = params["demand"]
    production_capacity = params["production_capacity"]

    months = list(range(len(demand)))

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=months)

    model.produce = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.order = pyo.Var(model.T, within=pyo.Binary)
    model.inventory = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.T, within=pyo.NonNegativeReals)

    def prod_cap_rule(mdl, t):
        return mdl.produce[t] <= production_capacity * mdl.order[t]
    model.prod_cap = pyo.Constraint(model.T, rule=prod_cap_rule)

    # Balance: I_t - B_t = I_{t-1} - B_{t-1} + produce_t - demand_t
    def balance_rule(mdl, t):
        prev_net = 0
        if t > 0:
            prev_net = mdl.inventory[t - 1] - mdl.backlog[t - 1]
        return mdl.inventory[t] - mdl.backlog[t] == prev_net + mdl.produce[t] - demand[t]
    model.balance = pyo.Constraint(model.T, rule=balance_rule)

    def obj_rule(mdl):
        return sum(
            production_cost[t] * mdl.produce[t]
            + fixed_order_cost[t] * mdl.order[t]
            + holding_cost[t] * mdl.inventory[t]
            + backlog_cost[t] * mdl.backlog[t]
            for t in mdl.T
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}