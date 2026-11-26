import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    cost_1 = params["cost_1"]
    cost_2 = params["cost_2"]
    cost_3 = params["cost_3"]
    cost_4 = params["cost_4"]

    months = [1, 2, 3, 4]
    costs = {1: cost_1, 2: cost_2, 3: cost_3, 4: cost_4}

    # Pairs (start_month, duration) for contracts that fit within the 4-month horizon
    contracts = [(s, d) for s in months for d in months if s + d - 1 <= 4]

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=months, dimen=1)
    model.C = pyo.Set(initialize=contracts, dimen=2)

    model.x = pyo.Var(model.C, domain=pyo.NonNegativeReals)

    def coverage_rule(m, t):
        return sum(
            m.x[s, d]
            for (s, d) in contracts
            if s <= t <= s + d - 1
        ) >= demand[t - 1]

    model.coverage = pyo.Constraint(model.S, rule=coverage_rule)

    def obj_rule(m):
        return sum(costs[d] * m.x[s, d] for (s, d) in contracts)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}