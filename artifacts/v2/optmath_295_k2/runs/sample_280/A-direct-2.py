import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_factories = len(activation_cost)
    n_months = len(demand)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_factories - 1)
    model.M = pyo.RangeSet(0, n_months - 1)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(
            activation_cost[f] * m.run[f, t] + production_cost[f] * m.prod[f, t]
            for f in m.F
            for t in m.M
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def min_rule(m, f, t):
        return m.prod[f, t] >= min_production[f] * m.run[f, t]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(m, f, t):
        return m.prod[f, t] <= max_production[f] * m.run[f, t]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}