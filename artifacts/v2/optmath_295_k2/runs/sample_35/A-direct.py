import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_capacity = params["production_capacity"]

    n = len(profit)
    item_ids = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_ids)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals,
                      bounds=lambda model, i: (0, production_capacity[i]))

    def obj_rule(model):
        return sum(profit[i] * model.x[i] for i in model.item_set)

    model.profit_obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def resource_rule(model):
        return sum(resource_consumption[i] * model.x[i] for i in model.item_set) <= resource_capacity

    model.resource_con = pyo.Constraint(rule=resource_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit_obj))

    return {"objective": obj_val, "status": "optimal"}