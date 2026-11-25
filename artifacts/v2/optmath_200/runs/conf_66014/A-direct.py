import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_capacities = params["resource_capacities"]
    resource_budget = params["resource_budget"]
    production_limits = params["production_limits"]

    n = len(profit_margins)

    model = pyo.ConcreteModel()
    model.items = pyo.RangeSet(0, n - 1)

    model.produce = pyo.Var(model.items, within=pyo.NonNegativeReals)

    def profit_rule(mdl):
        return sum(profit_margins[i] * mdl.produce[i] for i in mdl.items)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def resource_rule(mdl):
        return sum(resource_capacities[i] * mdl.produce[i] for i in mdl.items) <= resource_budget

    model.resource_con = pyo.Constraint(rule=resource_rule)

    def upper_rule(mdl, i):
        return mdl.produce[i] <= production_limits[i]

    model.upper_con = pyo.Constraint(model.items, rule=upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}