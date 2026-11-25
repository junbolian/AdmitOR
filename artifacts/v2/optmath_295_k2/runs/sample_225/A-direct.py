import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    months = list(range(6))
    products = ["A", "B"]

    demand_A = params["cumulative_demand_A"]
    demand_B = params["cumulative_demand_B"]
    prod_cost_A = params["production_cost_A"]
    prod_cost_B = params["production_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["holding_cost_A"]
    hold_cost_B = params["holding_cost_B"]
    usage_A = params["resource_usage_A"]
    usage_B = params["resource_usage_B"]
    capacity = params["resource_capacity"]

    cum_demand = {"A": demand_A, "B": demand_B}
    prod_cost = {"A": prod_cost_A, "B": prod_cost_B}
    setup_cost = {"A": setup_cost_A, "B": setup_cost_B}
    hold_cost = {"A": hold_cost_A, "B": hold_cost_B}
    usage = {"A": usage_A, "B": usage_B}

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=months, ordered=True)
    model.P = pyo.Set(initialize=products, ordered=True)

    model.x = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.M, domain=pyo.Binary)

    # Big-M upper bound for production: cumulative demand from month onward
    def bigM(p, t):
        total = cum_demand[p][len(cum_demand[p]) - 1]
        prev = cum_demand[p][t - 1] if t > 0 else 0
        return total - prev

    def prod_upper(m, p, t):
        return m.x[p, t] <= bigM(p, t) * m.y[p, t]

    model.prod_upper = pyo.Constraint(model.P, model.M, rule=prod_upper)

    # Inventory balance: no initial or final inventory
    def inv_balance(m, p, t):
        prev_inv = m.inv[p, t - 1] if t > 0 else 0
        demand_t = cum_demand[p][t] - (cum_demand[p][t - 1] if t > 0 else 0)
        return m.inv[p, t] == prev_inv + m.x[p, t] - demand_t

    model.inv_balance = pyo.Constraint(model.P, model.M, rule=inv_balance)

    # Cumulative demand satisfaction through final month
    def cum_demand_rule(m, p, t):
        return sum(m.x[p, s] for s in m.M if s <= t) >= cum_demand[p][t]

    model.cum_demand = pyo.Constraint(model.P, model.M, rule=cum_demand_rule)

    # No inventory at end of horizon
    def final_inv(m, p):
        return m.inv[p, len(months) - 1] == 0

    model.final_inv = pyo.Constraint(model.P, rule=final_inv)

    # Resource capacity
    def res_cap(m, t):
        return usage_A * m.x["A", t] + usage_B * m.x["B", t] <= capacity[t]

    model.res_cap = pyo.Constraint(model.M, rule=res_cap)

    # Objective
    def obj_rule(m):
        total = 0
        for p in products:
            for t in months:
                total += prod_cost[p][t] * m.x[p, t]
                total += setup_cost[p][t] * m.y[p, t]
                total += hold_cost[p][t] * m.inv[p, t]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}