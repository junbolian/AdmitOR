import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.destinations = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.origins, model.destinations, within=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.destinations) <= supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) >= demand[j]

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)
    model.cap_con = pyo.Constraint(model.origins, model.destinations, rule=cap_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.origins for j in model.destinations),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}