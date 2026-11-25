import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = list(range(7))

    demand_A = params["demand_A"]
    demand_B = params["demand_B"]
    prod_cost_A = params["prod_cost_A"]
    prod_cost_B = params["prod_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["hold_cost_A"]
    hold_cost_B = params["hold_cost_B"]
    resource_usage_A = params["resource_usage_A"]
    resource_usage_B = params["resource_usage_B"]
    resource_capacity = params["resource_capacity"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)

    model.xA = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.yA = pyo.Var(model.P, domain=pyo.Binary)
    model.yB = pyo.Var(model.P, domain=pyo.Binary)
    model.IA = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.IB = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    # Deterministic per-period demand from cumulative demands
    def demand_rate(cumulative, t):
        if t == 0:
            return cumulative[0]
        return cumulative[t] - cumulative[t - 1]

    demand_A_t = {t: demand_rate(demand_A, t) for t in periods}
    demand_B_t = {t: demand_rate(demand_B, t) for t in periods}

    # Big-M bounds on production due to resource capacity
    def bigM_A(t):
        return resource_capacity[t] / resource_usage_A

    def bigM_B(t):
        return resource_capacity[t] / resource_usage_B

    def prod_A_bound(mdl, t):
        return mdl.xA[t] <= bigM_A(t) * mdl.yA[t]

    def prod_B_bound(mdl, t):
        return mdl.xB[t] <= bigM_B(t) * mdl.yB[t]

    model.prod_A_bound = pyo.Constraint(model.P, rule=prod_A_bound)
    model.prod_B_bound = pyo.Constraint(model.P, rule=prod_B_bound)

    # Resource capacity constraint
    def resource_rule(mdl, t):
        return (resource_usage_A * mdl.xA[t] + resource_usage_B * mdl.xB[t]
                <= resource_capacity[t])

    model.resource_rule = pyo.Constraint(model.P, rule=resource_rule)

    # Inventory balance
    def bal_A(mdl, t):
        prev = mdl.IA[t - 1] if t > 0 else 0.0
        return mdl.IA[t] == prev + mdl.xA[t] - demand_A_t[t]

    def bal_B(mdl, t):
        prev = mdl.IB[t - 1] if t > 0 else 0.0
        return mdl.IB[t] == prev + mdl.xB[t] - demand_B_t[t]

    model.bal_A = pyo.Constraint(model.P, rule=bal_A)
    model.bal_B = pyo.Constraint(model.P, rule=bal_B)

    # Objective: production + setup + holding costs
    def obj_rule(mdl):
        return sum(
            prod_cost_A[t] * mdl.xA[t]
            + prod_cost_B[t] * mdl.xB[t]
            + setup_cost_A[t] * mdl.yA[t]
            + setup_cost_B[t] * mdl.yB[t]
            + hold_cost_A[t] * mdl.IA[t]
            + hold_cost_B[t] * mdl.IB[t]
            for t in mdl.P
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}