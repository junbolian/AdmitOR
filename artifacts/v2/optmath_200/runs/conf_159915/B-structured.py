# IR: {"sets":{"I":"0..6","J":"0..5"},"params":{"supply":"supply[I]","demand":"demand[J]","cost":"cost[I,J]","capacity":"capacity[I,J]"},"variables":{"x[I,J]":"nonnegative continuous"},"constraints":["sum(j in J, x[i,j]) <= supply[i] for i in I","sum(i in I, x[i,j]) == demand[j] for j in J","x[i,j] <= capacity[i,j] for (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, cost[i,j]*x[i,j])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based supply/demand arrays and cost/capacity matrices."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
    )

    model.x = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_limits = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.x[i, j] for j in mdl.destinations
        ) <= mdl.supply[i],
    )
    model.demand_requirements = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.x[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )
    model.transport_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.capacity[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}