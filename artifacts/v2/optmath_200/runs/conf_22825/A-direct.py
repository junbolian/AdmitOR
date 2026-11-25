import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    time_per_unit = params["time_per_unit"]
    total_capacity_hours = params["total_capacity_hours"]
    min_demand = params["min_demand"]
    max_demand = params["max_demand"]

    n = len(profit_per_unit)
    products = list(range(n))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit_per_unit[i] * m.x[i] for i in m.P)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def capacity_rule(m):
        return sum(time_per_unit[i] * m.x[i] for i in m.P) <= total_capacity_hours

    model.capacity = pyo.Constraint(rule=capacity_rule)

    def min_rule(m, i):
        return m.x[i] >= min_demand[i]

    model.min_demand_con = pyo.Constraint(model.P, rule=min_rule)

    def max_rule(m, i):
        return m.x[i] <= max_demand[i]

    model.max_demand_con = pyo.Constraint(model.P, rule=max_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))

    return {"objective": obj_val, "status": "optimal"}