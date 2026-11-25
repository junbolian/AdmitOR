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
    model.dests = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.origins, model.dests, domain=pyo.NonNegativeReals)

    def cap_bound(i, j):
        key = (i, j)
        if key in capacity and capacity[key] is not None:
            return capacity[key]
        return min(supply[i], demand[j])

    model.cap = pyo.Constraint(model.origins, model.dests,
                               rule=lambda m, i, j: m.x[i, j] <= cap_bound(i, j))

    model.supply_con = pyo.Constraint(model.origins,
                                      rule=lambda m, i: sum(m.x[i, j] for j in m.dests) == supply[i])

    model.demand_con = pyo.Constraint(model.dests,
                                      rule=lambda m, j: sum(m.x[i, j] for i in m.origins) == demand[j])

    model.obj = pyo.Objective(expr=sum(cost[i][j] * model.x[i, j]
                                       for i in model.origins for j in model.dests),
                              sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}