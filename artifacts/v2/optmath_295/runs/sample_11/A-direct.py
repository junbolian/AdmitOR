import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_capacities = params["production_capacities"]

    item_indices = list(range(len(profit_margins)))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_indices)

    model.quantity = pyo.Var(model.item_set, within=pyo.NonNegativeReals)

    def quantity_bounds_rule(m, i):
        return (0, production_capacities[i])
    model.quantity_bounds = pyo.Constraint(model.item_set, rule=quantity_bounds_rule)

    def resource_rule(m):
        return sum(resource_coefficients[i] * m.quantity[i] for i in m.item_set) <= resource_capacity
    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def objective_rule(m):
        return sum(profit_margins[i] * m.quantity[i] for i in m.item_set)
    model.profit_objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_objective))
    return {'objective': obj_val, 'status': 'optimal'}