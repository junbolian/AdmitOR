import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 5
    products = ["A", "B"]

    demand_A = params["demand_A"]
    demand_B = params["demand_B"]
    prod_cost_A = params["prod_cost_A"]
    prod_cost_B = params["prod_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["hold_cost_A"]
    hold_cost_B = params["hold_cost_B"]
    resource_use_A = params["resource_use_A"]
    resource_use_B = params["resource_use_B"]
    resource_capacity = params["resource_capacity"]
    max_prod_A = params["max_prod_A"]
    max_prod_B = params["max_prod_B"]

    demand = {"A": demand_A, "B": demand_B}
    prod_cost = {"A": prod_cost_A, "B": prod_cost_B}
    setup_cost = {"A": setup_cost_A, "B": setup_cost_B}
    hold_cost = {"A": hold_cost_A, "B": hold_cost_B}
    resource_use = {"A": resource_use_A, "B": resource_use_B}
    max_prod = {"A": max_prod_A, "B": max_prod_B}

    # Convert cumulative demands to per-period (incremental) demands
    incr_demand = {}
    for p in products:
        cum = demand[p]
        inc = []
        prev = 0.0
        for t in range(T):
            inc.append(cum[t] - prev)
            prev = cum[t]
        incr_demand[p] = inc

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, T - 1)
    model.P = pyo.Set(initialize=products)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.P, model.T, domain=pyo.Binary)

    def objective_rule(m):
        total = 0.0
        for p in products:
            for t in range(T):
                total += prod_cost[p][t] * m.prod[p, t]
                total += setup_cost[p][t] * m.setup[p, t]
                total += hold_cost[p][t] * m.inv[p, t]
        return total

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Inventory balance using per-period demand
    def balance_rule(m, p, t):
        prev = m.inv[p, t - 1] if t > 0 else 0.0
        return prev + m.prod[p, t] == incr_demand[p][t] + m.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def final_rule(m, p):
        return m.inv[p, T - 1] == 0.0

    model.final_inv = pyo.Constraint(model.P, rule=final_rule)

    def resource_rule(m, t):
        return (resource_use["A"] * m.prod["A", t]
                + resource_use["B"] * m.prod["B", t]) <= resource_capacity[t]

    model.resource = pyo.Constraint(model.T, rule=resource_rule)

    def maxprod_rule(m, p, t):
        return m.prod[p, t] <= max_prod[p][t] * m.setup[p, t]

    model.maxprod = pyo.Constraint(model.P, model.T, rule=maxprod_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}