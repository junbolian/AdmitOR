import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock = params["stock"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    n = len(stock)
    hospitals = list(range(n))

    model = pyo.ConcreteModel()
    model.hosp = pyo.Set(initialize=hospitals)

    # flow[i, j]: units shipped from hospital i to hospital j (i != j)
    model.flow = pyo.Var(model.hosp, model.hosp, domain=pyo.NonNegativeReals)

    # Fix diagonal to zero (no self-transfer)
    for i in hospitals:
        model.flow[i, i].fix(0)

    # Cost objective
    def cost_rule(mdl):
        return sum(
            transfer_cost[i][j] * mdl.flow[i, j]
            for i in hospitals
            for j in hospitals
            if i != j
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Each hospital's final stock must meet demand:
    # initial stock - outflow + inflow >= demand
    def balance_rule(mdl, i):
        outflow = sum(mdl.flow[i, j] for j in hospitals if j != i)
        inflow = sum(mdl.flow[j, i] for j in hospitals if j != i)
        return stock[i] - outflow + inflow >= demand[i]

    model.balance = pyo.Constraint(model.hosp, rule=balance_rule)

    # Cannot ship more than available initial stock out of a hospital
    def supply_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in hospitals if j != i) <= stock[i]

    model.supply_limit = pyo.Constraint(model.hosp, rule=supply_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}