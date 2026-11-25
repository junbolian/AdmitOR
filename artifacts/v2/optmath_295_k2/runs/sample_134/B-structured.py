# IR: {"sets":{"A":"range(params['num_aircraft_types'])","R":"range(params['num_routes'])"},"params":{"availability":"availability[a], a in A","demand":"demand[r], r in R","cost":"cost[a][r], (a,r) in A x R","capability":"capability[a][r], (a,r) in A x R","num_aircraft_types":"params['num_aircraft_types']","num_routes":"params['num_routes']"},"variables":{"x[a,r]":"nonnegative integer, (a,r) in A x R"},"constraints":["sum(x[a,r] for r in R) <= availability[a], for a in A","sum(capability[a,r]*x[a,r] for a in A) >= demand[r], for r in R"],"objective":"minimize sum(cost[a,r]*x[a,r] for (a,r) in A x R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_aircraft_types = params["num_aircraft_types"]
    num_routes = params["num_routes"]
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capability = params["capability"]

    model = pyo.ConcreteModel()

    model.aircraft_types = pyo.Set(
        initialize=range(num_aircraft_types), ordered=True
    )
    model.routes = pyo.Set(initialize=range(num_routes), ordered=True)

    model.availability = pyo.Param(
        model.aircraft_types,
        initialize=lambda _, aircraft: availability[aircraft],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda _, route: demand[route],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda _, aircraft, route: cost[aircraft][route],
        within=pyo.Reals,
    )
    model.capability = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda _, aircraft, route: capability[aircraft][route],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(instance, aircraft):
        return (
            sum(instance.x[aircraft, route] for route in instance.routes)
            <= instance.availability[aircraft]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types, rule=availability_rule
    )

    def demand_rule(instance, route):
        return (
            sum(
                instance.capability[aircraft, route]
                * instance.x[aircraft, route]
                for aircraft in instance.aircraft_types
            )
            >= instance.demand[route]
        )

    model.route_requirements = pyo.Constraint(model.routes, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft, route] * model.x[aircraft, route]
            for aircraft in model.aircraft_types
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Other runtime errors are unexpected and must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}