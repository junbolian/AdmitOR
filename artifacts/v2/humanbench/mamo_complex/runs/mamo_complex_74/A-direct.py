import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    regular_capacity = params["regular_capacity"]
    regular_cost = params["regular_cost"]
    overtime_capacity = params["overtime_capacity"]
    overtime_cost = params["overtime_cost"]
    holding_cost = params["holding_cost"]
    initial_inventory = params["initial_inventory"]

    n = len(demand)
    months = list(range(n))

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=months)

    model.reg = pyo.Var(model.M, within=pyo.NonNegativeReals, bounds=(0, regular_capacity))
    model.ot = pyo.Var(model.M, within=pyo.NonNegativeReals, bounds=(0, overtime_capacity))
    model.inv = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def inv_balance_rule(m, t):
        prev = initial_inventory if t == 0 else m.inv[t - 1]
        return prev + m.reg[t] + m.ot[t] - m.inv[t] == demand[t]
    model.inv_balance = pyo.Constraint(model.M, rule=inv_balance_rule)

    def cost_rule(m):
        return sum(regular_cost * m.reg[t] + overtime_cost * m.ot[t] + holding_cost * m.inv[t]
                   for t in m.M)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}