# IR: {"sets":{"I":"0..5","J":"0..6"},"params":{"capacity":"params['capacity'][i]","demand":"params['demand'][j]","min_delivery":"params['min_delivery'][i]","cost":"params['cost'][i][j]","min_producers":"params['min_producers'][j]"},"variables":{"x[i,j]":"NonNegativeReals; electricity delivered","y[i,j]":"Binary; producer selected"},"constraints":["sum_j x[i,j] <= capacity[i] for each i","sum_i x[i,j] >= demand[j] for each j","sum_i y[i,j] >= min_producers[j] for each j","x[i,j] >= min_delivery[i]*y[i,j] for each i,j","x[i,j] <= capacity[i]*y[i,j] for each i,j"],"objective":"minimize sum_i sum_j cost[i,j]*x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed sequences or integer-keyed mappings in params."""
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 6)

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
    model.min_producers = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["min_producers"][j],
        within=pyo.NonNegativeIntegers,
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
    model.selection_limits = pyo.Constraint(
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
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}