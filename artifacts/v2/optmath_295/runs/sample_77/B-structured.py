# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"aircraft_availability":"A[i]","route_demand":"D[j]","cost_matrix":"C[i,j]","capacity_matrix":"Q[i,j]"},"variables":{"x[i,j]":{"type":"nonnegative_integer","meaning":"number of aircraft of type i assigned to route j"}},"constraints":["sum(j in J, x[i,j]) <= A[i] for each i in I","sum(i in I, Q[i,j]*x[i,j]) >= D[j] for each j in J"],"objective":"minimize sum(i in I, j in J, C[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, 7)
    model.routes = pyo.RangeSet(0, 7)

    model.availability = pyo.Param(
        model.aircraft,
        initialize=lambda mdl, i: aircraft_availability[i],
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: route_demand[j],
    )
    model.operating_cost = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
    )
    model.capacity = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda mdl, i, j: capacity_matrix[i][j],
    )

    model.x = pyo.Var(
        model.aircraft,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.aircraft,
        rule=availability_rule,
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft
            )
            >= mdl.demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[i, j] * model.x[i, j]
            for i in model.aircraft
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Still determine success exclusively by objective retrieval below.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}