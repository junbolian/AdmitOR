# IR: {"sets":{"aircraft_types":[0,1,2,3,4],"routes":[0,1,2,3,4]},"params":{"availability":"availability[i] from params['availability']","demand":"demand[j] from params['demand']","capacity":"capacity[i][j] from params['capacity']","cost":"cost[i][j] from params['cost']"},"variables":{"x[i,j]":"nonnegative integer aircraft assignments"},"constraints":["For each aircraft type i: sum_j x[i,j] <= availability[i]","For each route j: sum_i capacity[i,j]*x[i,j] >= demand[j]"],"objective":"Minimize sum_i sum_j cost[i,j]*x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using vectors indexed by type/route and matrices indexed [type][route]."""
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.aircraft_types = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 4)

    model.aircraft_availability = pyo.Param(
        model.aircraft_types,
        initialize=lambda mdl, i: availability[i],
        within=pyo.NonNegativeReals,
    )
    model.route_demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.passenger_capacity = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.aircraft_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.aircraft_types,
        rule=availability_rule,
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.passenger_capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft_types
            )
            >= mdl.route_demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.x[i, j]
            for i in model.aircraft_types
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi raises RuntimeError when it cannot load a feasible solution.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}