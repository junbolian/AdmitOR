# IR: {"sets":{"I":"1..7","J":"1..6"},"params":{"supply":"nonnegative vector[I]","demand":"nonnegative vector[J]","cost":"real matrix[I,J]","capacity":"nonnegative matrix[I,J]"},"variables":{"flow[I,J]":"nonnegative continuous"},"constraints":["sum(flow[i,j] for j in J) <= supply[i] for each i in I","sum(flow[i,j] for i in I) == demand[j] for each j in J","flow[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(cost[i,j] * flow[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input vectors and nested row-major matrices."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(1, 7)
    model.destinations = pyo.RangeSet(1, 6)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i - 1][j - 1],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_limits = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.flow[i, j] for j in mdl.destinations
        ) <= mdl.supply[i],
    )
    model.demand_requirements = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.flow[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )
    model.arc_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.flow[i, j] <= mdl.capacity[i, j],
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
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}