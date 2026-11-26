import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    cities = list(range(len(supply)))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=cities, ordered=True)

    # Flow variables: x[i,j] units shipped from i to j (diagonal excluded).
    off_diag = [(i, j) for i in cities for j in cities if i != j]
    model.od = pyo.Set(initialize=off_diag, dimen=2)
    model.x = pyo.Var(model.od, domain=pyo.NonNegativeReals)

    # Objective: minimize total transfer cost.
    def cost_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.od)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Each city's final holdings must be at least its demand.
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    def balance_rule(m, c):
        inflow = sum(m.x[i, c] for i in cities if i != c)
        outflow = sum(m.x[c, j] for j in cities if j != c)
        return supply[c] + inflow - outflow >= demand[c]
    model.balance = pyo.Constraint(model.C, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}