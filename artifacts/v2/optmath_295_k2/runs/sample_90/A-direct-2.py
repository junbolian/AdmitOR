import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_dests = len(demand)

    model = pyo.ConcreteModel()

    model.origin_set = pyo.RangeSet(0, n_origins - 1)
    model.dest_set = pyo.RangeSet(0, n_dests - 1)

    model.flow = pyo.Var(model.origin_set, model.dest_set, within=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in mdl.dest_set) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.flow[i, j] for i in mdl.origin_set) == demand[j]

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity[i][j]

    model.supply_con = pyo.Constraint(model.origin_set, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.dest_set, rule=demand_rule)
    model.capacity_con = pyo.Constraint(model.origin_set, model.dest_set, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.flow[i, j]
                 for i in model.origin_set
                 for j in model.dest_set),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}