import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    clinics = list(range(n))
    pairs = [(i, j) for i in clinics for j in clinics if i != j]

    model = pyo.ConcreteModel()
    model.clinics = pyo.Set(initialize=clinics)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j] for (i, j) in m.pairs)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(m, k):
        inflow = sum(m.x[i, k] for (i, j) in m.pairs if j == k)
        outflow = sum(m.x[k, j] for (i, j) in m.pairs if i == k)
        return supply[k] + inflow - outflow == demand[k]
    model.balance = pyo.Constraint(model.clinics, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}