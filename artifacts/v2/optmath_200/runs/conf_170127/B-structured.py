# IR: {"sets":{"aircraft":"0..10","routes":"0..6"},"params":{"availability":"params['availability'][i], nonnegative integer","demand":"params['demand'][j], nonnegative real","capacity":"params['capacity'][i][j], nonnegative real","cost":"params['cost'][i][j], real","input_indexing":"Sequences or mappings keyed by integer indices, string indices, or aircraft_i/route_j labels"},"variables":{"assignment[i,j]":"integer, 0 <= assignment[i,j] <= availability[i]"},"constraints":["For each aircraft i: sum_j assignment[i,j] <= availability[i]","For each route j: sum_i capacity[i,j]*assignment[i,j] >= demand[j]"],"objective":"Minimize sum_i sum_j cost[i,j]*assignment[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, prefix):
    """Read an indexed value without assuming mapping keys are integers."""
    if isinstance(data, Mapping):
        for key in (position, str(position), f"{prefix}_{position}"):
            if key in data:
                return data[key]
        raise KeyError(f"Missing {prefix}_{position}")
    return data[position]


def solve(params):
    availability_data = params["availability"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]

    model = pyo.ConcreteModel()

    model.aircraft = pyo.RangeSet(0, 10)
    model.routes = pyo.RangeSet(0, 6)

    model.availability = pyo.Param(
        model.aircraft,
        initialize=lambda mdl, i: _entry(availability_data, i, "aircraft"),
        within=pyo.NonNegativeIntegers,
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: _entry(demand_data, j, "route"),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda mdl, i, j: _entry(
            _entry(capacity_data, i, "aircraft"), j, "route"
        ),
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda mdl, i, j: _entry(
            _entry(cost_data, i, "aircraft"), j, "route"
        ),
        within=pyo.Reals,
    )

    def assignment_bounds(mdl, i, j):
        return (0, mdl.availability[i])

    model.assignment = pyo.Var(
        model.aircraft,
        model.routes,
        domain=pyo.NonNegativeIntegers,
        bounds=assignment_bounds,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.assignment[i, j] for j in mdl.routes)
            <= mdl.availability[i]
        )

    model.availability_limit = pyo.Constraint(
        model.aircraft,
        rule=availability_rule,
    )

    def coverage_rule(mdl, j):
        return (
            sum(
                mdl.capacity[i, j] * mdl.assignment[i, j]
                for i in mdl.aircraft
            )
            >= mdl.demand[j]
        )

    model.route_coverage = pyo.Constraint(
        model.routes,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.assignment[i, j]
            for i in model.aircraft
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Allow objective retrieval to determine success when HiGHS
        # reports that it could not load a feasible solution.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}