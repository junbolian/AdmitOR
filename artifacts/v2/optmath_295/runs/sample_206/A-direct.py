import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    transport_limit = params["transport_limit"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.dests = pyo.RangeSet(0, n_dest - 1)

    model.flow = pyo.Var(model.origins, model.dests, domain=pyo.NonNegativeReals)

    def flow_bound(mdl, i, j):
        return (0, transport_limit[i][j])

    model.flow_bounds = pyo.Constraint(model.origins, model.dests, rule=flow_bound)

    def supply_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in mdl.dests) <= supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.flow[i, j] for i in mdl.origins) == demand[j]

    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    def obj_rule(mdl):
        return sum(
            transport_cost[i][j] * mdl.flow[i, j]
            for i in mdl.origins
            for j in mdl.dests
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}