import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_budget = params["resource_budget"]
    production_capacities = params["production_capacities"]

    n = len(profit_margins)

    model = pyo.ConcreteModel()

    model.item_set = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    def capacity_rule(m, i):
        return m.x[i] <= production_capacities[i]

    model.capacity_constraint = pyo.Constraint(model.item_set, rule=capacity_rule)

    def resource_rule(m):
        return sum(resource_consumption[i] * m.x[i] for i in m.item_set) <= resource_budget

    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def objective_rule(m):
        return sum(profit_margins[i] * m.x[i] for i in m.item_set)

    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}