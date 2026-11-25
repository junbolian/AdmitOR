# IR: {"sets":{"origins":"0..6","destinations":"0..6"},"params":{"supply":"supply[i] >= 0","demand":"demand[j] >= 0","cost":"cost[i][j] real","capacity":"capacity[i][j] >= 0"},"variables":{"flow[i,j]":"continuous nonnegative"},"constraints":["sum_j flow[i,j] <= supply[i] for each origin i","sum_i flow[i,j] == demand[j] for each destination j","flow[i,j] <= capacity[i][j] for each arc (i,j)"],"objective":"minimize sum_i sum_j cost[i][j] * flow[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.flow[i, j] for j in mdl.destinations)
            <= mdl.supply[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.flow[i, j] for i in mdl.origins)
            == mdl.demand[j]
        )

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.arc_capacity[i, j]

    model.supply_limits = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_requirements = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
    model.capacity_limits = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.flow[i, j]
            for i in model.origins
            for j in model.destinations
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