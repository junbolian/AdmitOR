import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    products = range(3)
    months = range(6)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(products))
    model.M = pyo.Set(initialize=list(months))

    model.x = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.M, domain=pyo.Binary)
    model.inv = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return (
            sum(production_cost[p][t] * m.x[p, t] for p in m.P for t in m.M)
            + sum(setup_cost[p][t] * m.y[p, t] for p in m.P for t in m.M)
            + sum(holding_cost[p] * m.inv[p, t] for p in m.P for t in m.M)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, t):
        return sum(capacity_consumption[p] * m.x[p, t] for p in m.P) <= capacity[t]

    model.capacity_con = pyo.Constraint(model.M, rule=cap_rule)

    def bigm_rule(m, p, t):
        cum_demand = sum(demand[p][k] for k in range(t, 6))
        return m.x[p, t] <= cum_demand * m.y[p, t]

    model.bigm_con = pyo.Constraint(model.P, model.M, rule=bigm_rule)

    def balance_first_rule(m, p):
        return m.x[p, 0] - m.inv[p, 0] == demand[p][0]

    def balance_rule(m, p, t):
        return m.inv[p, t - 1] + m.x[p, t] - m.inv[p, t] == demand[p][t]

    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)
    model.balance = pyo.Constraint(
        model.P,
        pyo.Set(initialize=[t for t in months if t >= 1]),
        rule=balance_rule,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}