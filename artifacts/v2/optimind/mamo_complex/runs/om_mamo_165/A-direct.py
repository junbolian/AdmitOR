import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_stock = params["initial_stock"]
    required_supplies = params["required_supplies"]
    transfer_costs = params["transfer_costs"]

    n = len(initial_stock)
    hospitals = list(range(n))
    pairs = [(i, j) for i in hospitals for j in hospitals if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def supply_balance_rule(m, i):
        inflow = sum(m.x[j, i] for j in hospitals if j != i)
        outflow = sum(m.x[i, j] for j in hospitals if j != i)
        return initial_stock[i] + inflow - outflow >= required_supplies[i]

    model.supply_balance = pyo.Constraint(hospitals, rule=supply_balance_rule)

    def obj_rule(m):
        return sum(transfer_costs[i][j] * m.x[i, j] for (i, j) in pairs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}