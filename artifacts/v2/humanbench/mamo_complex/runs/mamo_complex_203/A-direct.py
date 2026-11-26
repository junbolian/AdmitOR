import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    transport_cost = params["transport_cost"]
    current_supply = params["current_supply"]
    demand = params["demand"]

    regions = list(range(5))

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions)
    model.pairs = pyo.Set(initialize=[(i, j) for i in regions for j in regions if i != j])

    model.x = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j] for (i, j) in m.pairs)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(m, r):
        inflow = sum(m.x[i, r] for i in regions if i != r)
        outflow = sum(m.x[r, j] for j in regions if j != r)
        return current_supply[r] + inflow - outflow >= demand[r]
    model.balance = pyo.Constraint(model.regions, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}