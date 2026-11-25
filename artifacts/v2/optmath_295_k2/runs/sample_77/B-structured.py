# IR: {"sets":{"A":"0..7","R":"0..7"},"params":{"costs":"A x R, from params","capacities":"A x R, from params","aircraft_availability":"A, from params","route_demand":"R, from params"},"variables":{"x[a,r]":"nonnegative integer assignment count"},"constraints":["For each a in A: sum(r in R, x[a,r]) <= aircraft_availability[a]","For each r in R: sum(a in A, capacities[a,r]*x[a,r]) >= route_demand[r]"],"objective":"Minimize sum(a in A, r in R, costs[a,r]*x[a,r])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    capacities = params["capacities"]
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]

    model = pyo.ConcreteModel()
    model.A = pyo.RangeSet(0, 7)
    model.R = pyo.RangeSet(0, 7)

    model.costs = pyo.Param(
        model.A,
        model.R,
        initialize=lambda mdl, a, r: costs[a][r],
        within=pyo.Reals,
    )
    model.capacities = pyo.Param(
        model.A,
        model.R,
        initialize=lambda mdl, a, r: capacities[a][r],
        within=pyo.NonNegativeReals,
    )
    model.aircraft_availability = pyo.Param(
        model.A,
        initialize=lambda mdl, a: aircraft_availability[a],
        within=pyo.NonNegativeReals,
    )
    model.route_demand = pyo.Param(
        model.R,
        initialize=lambda mdl, r: route_demand[r],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(mdl, a):
        return (
            sum(mdl.x[a, r] for r in mdl.R)
            <= mdl.aircraft_availability[a]
        )

    model.availability_constraints = pyo.Constraint(
        model.A, rule=availability_rule
    )

    def demand_rule(mdl, r):
        return (
            sum(mdl.capacities[a, r] * mdl.x[a, r] for a in mdl.A)
            >= mdl.route_demand[r]
        )

    model.demand_constraints = pyo.Constraint(model.R, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[a, r] * model.x[a, r]
            for a in model.A
            for r in model.R
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