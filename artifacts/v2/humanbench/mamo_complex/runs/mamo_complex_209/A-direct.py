import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regular_cost = params["regular_cost"]
    overtime_cost = params["overtime_cost"]
    holding_cost = params["holding_cost"]
    regular_capacity = params["regular_capacity"]
    initial_inventory = params["initial_inventory"]
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.quarters = pyo.RangeSet(1, 4)

    model.regular = pyo.Var(model.quarters, within=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.quarters, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.quarters, within=pyo.NonNegativeReals)

    def regular_cap_rule(m, t):
        return m.regular[t] <= regular_capacity

    model.regular_cap_con = pyo.Constraint(model.quarters, rule=regular_cap_rule)

    def inventory_balance_rule(m, t):
        prev = initial_inventory if t == 1 else m.inventory[t - 1]
        return m.inventory[t] == prev + m.regular[t] + m.overtime[t] - demand[t - 1]

    model.balance_con = pyo.Constraint(model.quarters, rule=inventory_balance_rule)

    def obj_rule(m):
        return sum(
            regular_cost * m.regular[t]
            + overtime_cost * m.overtime[t]
            + holding_cost * m.inventory[t]
            for t in m.quarters
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}