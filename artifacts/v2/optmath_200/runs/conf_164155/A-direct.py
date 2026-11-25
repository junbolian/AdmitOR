import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    capacity = params["capacity"]
    resource_budget = params["resource_budget"]

    items = list(range(40))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=items)

    model.x = pyo.Var(model.item_set, within=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0.0, capacity[i]))

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.item_set)
    model.profit_obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def res_rule(m):
        return sum(resource_coeff[i] * m.x[i] for i in m.item_set) <= resource_budget
    model.resource_con = pyo.Constraint(rule=res_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_obj))
    return {"objective": obj_val, "status": "optimal"}