# IR: {"sets":{"A":"range(params['num_aircraft_types'])","R":"range(params['num_routes'])"},"params":{"num_aircraft_types":"aircraft index-set size","num_routes":"route index-set size","availability":"availability[a] for a in A","demand":"demand[r] for r in R","cost":"cost[a][r] for (a,r) in A x R","capability":"capability[a][r] for (a,r) in A x R"},"variables":{"x[a,r]":"nonnegative integer for (a,r) in A x R"},"constraints":["sum(x[a,r] for r in R) <= availability[a] for a in A","sum(capability[a,r]*x[a,r] for a in A) >= demand[r] for r in R"],"objective":"minimize sum(cost[a,r]*x[a,r] for (a,r) in A x R)"}

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

    model.A = pyo.Set(initialize=range(num_aircraft_types), ordered=True)
    model.R = pyo.Set(initialize=range(num_routes), ordered=True)

    model.availability = pyo.Param(
        model.A,
        initialize=lambda mdl, a: availability[a],
    )
    model.demand = pyo.Param(
        model.R,
        initialize=lambda mdl, r: demand[r],
    )
    model.cost = pyo.Param(
        model.A,
        model.R,
        initialize=lambda mdl, a, r: cost[a][r],
    )
    model.capability = pyo.Param(
        model.A,
        model.R,
        initialize=lambda mdl, a, r: capability[a][r],
    )

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(mdl, a):
        return (
            sum(mdl.x[a, r] for r in mdl.R)
            <= mdl.availability[a]
        )

    model.aircraft_limits = pyo.Constraint(
        model.A, rule=availability_rule
    )

    def demand_rule(mdl, r):
        return (
            sum(mdl.capability[a, r] * mdl.x[a, r] for a in mdl.A)
            >= mdl.demand[r]
        )

    model.route_requirements = pyo.Constraint(
        model.R, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[a, r] * model.x[a, r]
            for a in model.A
            for r in model.R
        ),
        sense=pyo.minimize,
    )

    # APPsi raises RuntimeError when a feasible solution cannot be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}