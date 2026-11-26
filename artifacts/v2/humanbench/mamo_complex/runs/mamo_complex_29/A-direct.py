import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = 5
    regions = range(n)

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=list(regions))
    model.J = pyo.Set(initialize=list(regions))

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) >= demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": obj_val, "status": "optimal"}