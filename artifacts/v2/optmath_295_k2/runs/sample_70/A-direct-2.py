import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    origins = list(range(len(supply)))
    destinations = list(range(len(demand)))

    model.x = pyo.Var(origins, destinations, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in origins for j in destinations),
        sense=pyo.minimize,
    )

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in destinations) == supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in origins) == demand[j]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)
    model.demand_con = pyo.Constraint(destinations, rule=demand_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or unbounded"}