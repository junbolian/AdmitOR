# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4]},"params":{"capacity":"capacity[i]","demand":"demand[j]","min_producers":"min_producers[j]","min_delivery":"min_delivery[i]","cost":"cost[i][j]"},"variables":{"x[i,j]":"continuous nonnegative electricity delivered","y[i,j]":"binary producer participation"},"constraints":["sum(j in J,x[i,j]) <= capacity[i] for i in I","sum(i in I,x[i,j]) >= demand[j] for j in J","sum(i in I,y[i,j]) >= min_producers[j] for j in J","x[i,j] >= min_delivery[i]*y[i,j] for i in I,j in J","x[i,j] <= capacity[i]*y[i,j] for i in I,j in J"],"objective":"minimize sum(i in I,j in J,cost[i][j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexable parameter vectors and a nested cost matrix."""
    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(5), ordered=True)
    model.J = pyo.Set(initialize=range(5), ordered=True)

    model.capacity = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.min_producers = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["min_producers"][j],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["min_delivery"][i],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, model.J, domain=pyo.Binary)

    model.capacity_limits = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.J) <= mdl.capacity[i]
        ),
    )
    model.demand_requirements = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.I) >= mdl.demand[j]
        ),
    )
    model.producer_requirements = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.y[i, j] for i in mdl.I) >= mdl.min_producers[j]
        ),
    )
    model.minimum_deliveries = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: (
            mdl.x[i, j] >= mdl.min_delivery[i] * mdl.y[i, j]
        ),
    )
    model.participation_links = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: (
            mdl.x[i, j] <= mdl.capacity[i] * mdl.y[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Unexpected solver exceptions propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}