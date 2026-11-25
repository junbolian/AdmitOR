import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 5
    periods = list(range(T))

    demand_A = params["demand_A_cumulative"]
    demand_B = params["demand_B_cumulative"]
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

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=periods, ordered=True)

    model.prod_A = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.prod_B = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv_A = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv_B = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup_A = pyo.Var(model.T, domain=pyo.Binary)
    model.setup_B = pyo.Var(model.T, domain=pyo.Binary)

    def obj_rule(m):
        return (
            sum(prod_cost_A[t] * m.prod_A[t] + prod_cost_B[t] * m.prod_B[t] for t in m.T)
            + sum(setup_cost_A[t] * m.setup_A[t] + setup_cost_B[t] * m.setup_B[t] for t in m.T)
            + sum(hold_cost_A[t] * m.inv_A[t] + hold_cost_B[t] * m.inv_B[t] for t in m.T)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_A_rule(m, t):
        if t == 0:
            return m.prod_A[t] - m.inv_A[t] == demand_A[t]
        return m.inv_A[t - 1] + m.prod_A[t] - m.inv_A[t] == demand_A[t] - demand_A[t - 1]

    def balance_B_rule(m, t):
        if t == 0:
            return m.prod_B[t] - m.inv_B[t] == demand_B[t]
        return m.inv_B[t - 1] + m.prod_B[t] - m.inv_B[t] == demand_B[t] - demand_B[t - 1]

    model.balance_A = pyo.Constraint(model.T, rule=balance_A_rule)
    model.balance_B = pyo.Constraint(model.T, rule=balance_B_rule)

    def final_inv_A_rule(m):
        return m.inv_A[T - 1] == 0

    def final_inv_B_rule(m):
        return m.inv_B[T - 1] == 0

    model.final_inv_A = pyo.Constraint(rule=final_inv_A_rule)
    model.final_inv_B = pyo.Constraint(rule=final_inv_B_rule)

    def resource_rule(m, t):
        return resource_use_A * m.prod_A[t] + resource_use_B * m.prod_B[t] <= resource_capacity[t]

    model.resource = pyo.Constraint(model.T, rule=resource_rule)

    def max_A_rule(m, t):
        return m.prod_A[t] <= max_prod_A[t] * m.setup_A[t]

    def max_B_rule(m, t):
        return m.prod_B[t] <= max_prod_B[t] * m.setup_B[t]

    model.max_A = pyo.Constraint(model.T, rule=max_A_rule)
    model.max_B = pyo.Constraint(model.T, rule=max_B_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}