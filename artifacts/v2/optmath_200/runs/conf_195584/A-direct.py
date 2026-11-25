import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    ship_limit = params["ship_limit"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.destinations = pyo.RangeSet(0, n_dest - 1)

    model.ship = pyo.Var(model.origins, model.destinations, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.ship[i, j] for i in m.origins for j in m.destinations)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def sup_rule(m, i):
        return sum(m.ship[i, j] for j in m.destinations) <= supply[i]
    model.sup_con = pyo.Constraint(model.origins, rule=sup_rule)

    def dem_rule(m, j):
        return sum(m.ship[i, j] for i in m.origins) == demand[j]
    model.dem_con = pyo.Constraint(model.destinations, rule=dem_rule)

    def lim_rule(m, i, j):
        return m.ship[i, j] <= ship_limit[i][j]
    model.lim_con = pyo.Constraint(model.origins, model.destinations, rule=lim_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}