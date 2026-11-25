import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    factories = range(4)
    months = range(3)

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.run[f, t] + variable_cost[f] * m.produce[f, t]
            for f in m.F
            for t in m.M
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(m, f, t):
        return m.produce[f, t] >= min_production[f] * m.run[f, t]
    model.min_con = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(m, f, t):
        return m.produce[f, t] <= max_production[f] * m.run[f, t]
    model.max_con = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.F) >= demand[t]
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}