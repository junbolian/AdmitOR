# IR: {"sets":{"origins":"0..7","destinations":"0..7"},"params":{"supply":"params['supply'][i], nonnegative real","demand":"params['demand'][j], nonnegative real","cost":"params['cost'][i][j], real","arc_capacity":"params['arc_capacity'][i][j], nonnegative real"},"variables":{"flow[i,j]":"nonnegative continuous"},"constraints":["For each origin i: sum_j flow[i,j] = supply[i].","For each destination j: sum_i flow[i,j] = demand[j].","For each arc (i,j): flow[i,j] <= arc_capacity[i,j]."],"objective":"Minimize sum_i sum_j cost[i,j] * flow[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    arc_capacity = params["arc_capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 7)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): arc_capacity[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in mdl.destinations) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.flow[i, j] for i in mdl.origins) == mdl.demand[j]

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.arc_capacity[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.capacity_limits = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when automatic solution loading has no solution.
        # Propagate unrelated errors; assess success only through the objective.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}