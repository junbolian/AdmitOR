# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4,5],"P":[0,1]},"params":{"supply_p0":"O -> nonnegative real","supply_p1":"O -> nonnegative real","demand_p0":"D -> nonnegative real","demand_p1":"D -> nonnegative real","cost_p0":"O x D -> real","cost_p1":"O x D -> real","route_capacity":"O x D -> nonnegative real"},"variables":{"ship[o,d,p]":"nonnegative continuous"},"constraints":{"supply":"sum_d ship[o,d,p] <= supply_p[p][o], for all o,p","demand":"sum_o ship[o,d,p] == demand_p[p][d], for all d,p","capacity":"sum_p ship[o,d,p] <= route_capacity[o][d], for all o,d"},"objective":"minimize sum_o,d,p cost_p[p][o][d] * ship[o,d,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = {
        0: params["supply_p0"],
        1: params["supply_p1"],
    }
    demand = {
        0: params["demand_p0"],
        1: params["demand_p1"],
    }
    cost = {
        0: params["cost_p0"],
        1: params["cost_p1"],
    }
    route_capacity = params["route_capacity"]

    model = pyo.ConcreteModel()
    model.O = pyo.RangeSet(0, 3)
    model.D = pyo.RangeSet(0, 5)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.O,
        model.P,
        initialize=lambda mdl, o, p: supply[p][o],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.D,
        model.P,
        initialize=lambda mdl, d, p: demand[p][d],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.O,
        model.D,
        model.P,
        initialize=lambda mdl, o, d, p: cost[p][o][d],
        within=pyo.Reals,
    )
    model.route_limit = pyo.Param(
        model.O,
        model.D,
        initialize=lambda mdl, o, d: route_capacity[o][d],
        within=pyo.NonNegativeReals,
    )

    model.ship = pyo.Var(
        model.O, model.D, model.P, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, o, p):
        return sum(mdl.ship[o, d, p] for d in mdl.D) <= mdl.supply[o, p]

    def demand_rule(mdl, d, p):
        return sum(mdl.ship[o, d, p] for o in mdl.O) == mdl.demand[d, p]

    def capacity_rule(mdl, o, d):
        return sum(mdl.ship[o, d, p] for p in mdl.P) <= mdl.route_limit[o, d]

    model.supply_constraints = pyo.Constraint(
        model.O, model.P, rule=supply_rule
    )
    model.demand_constraints = pyo.Constraint(
        model.D, model.P, rule=demand_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.O, model.D, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[o, d, p] * model.ship[o, d, p]
            for o in model.O
            for d in model.D
            for p in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}