import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit)
    products = range(n)

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=list(products))

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals, bounds=lambda m, i: (min_production[i], max_production[i]))

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.P)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def time_rule(m):
        return sum(time_per_unit[i] * m.x[i] for i in m.P) <= time_capacity

    model.time_con = pyo.Constraint(rule=time_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}