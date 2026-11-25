import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    products = list(range(11))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals)

    def time_rule(mdl):
        return sum(time_per_unit[i] * mdl.x[i] for i in mdl.P) <= time_capacity

    model.time_constraint = pyo.Constraint(rule=time_rule)

    def min_rule(mdl, i):
        return mdl.x[i] >= min_production[i]

    model.min_constraint = pyo.Constraint(model.P, rule=min_rule)

    def max_rule(mdl, i):
        return mdl.x[i] <= max_production[i]

    model.max_constraint = pyo.Constraint(model.P, rule=max_rule)

    def obj_rule(mdl):
        return sum(profit[i] * mdl.x[i] for i in mdl.P)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    objective_value = float(pyo.value(model.obj))

    return {"objective": objective_value, "status": "optimal"}