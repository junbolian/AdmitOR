# IR: {"sets":{"A":"0..7","R":"0..7"},"params":{"costs":"A x R matrix","capacities":"A x R matrix","aircraft_availability":"A vector","route_demand":"R vector"},"variables":{"x[a,r]":"nonnegative integer assignment count"},"constraints":["forall a in A: sum(r in R, x[a,r]) <= aircraft_availability[a]","forall r in R: sum(a in A, capacities[a,r]*x[a,r]) >= route_demand[r]"],"objective":"minimize sum(a in A, r in R, costs[a,r]*x[a,r])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    capacities = params["capacities"]
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, 7)
    model.routes = pyo.RangeSet(0, 7)

    model.x = pyo.Var(
        model.aircraft,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(model, aircraft):
        return (
            sum(model.x[aircraft, route] for route in model.routes)
            <= aircraft_availability[aircraft]
        )

    model.availability_constraints = pyo.Constraint(
        model.aircraft,
        rule=availability_rule,
    )

    def demand_rule(model, route):
        return (
            sum(
                capacities[aircraft][route] * model.x[aircraft, route]
                for aircraft in model.aircraft
            )
            >= route_demand[route]
        )

    model.demand_constraints = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            costs[aircraft][route] * model.x[aircraft, route]
            for aircraft in model.aircraft
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}