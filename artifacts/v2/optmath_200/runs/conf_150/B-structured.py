# IR: {"sets":{"I":[0,1,2,3,4,5],"J":[0,1,2]},"params":{"aircraft_availability":"A[i], read from params","route_demand":"D[j], read from params","capacity":"P[i,j], read from params","cost":"C[i,j], read from params"},"variables":{"x[i,j]":"nonnegative integer aircraft assignments"},"constraints":["For each i in I: sum(x[i,j] for j in J) <= A[i]","For each j in J: sum(P[i,j]*x[i,j] for i in I) >= D[j]"],"objective":"minimize sum(C[i,j]*x[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 2)

    model.A = pyo.Param(
        model.I,
        initialize=lambda mdl, i: aircraft_availability[i],
    )
    model.D = pyo.Param(
        model.J,
        initialize=lambda mdl, j: route_demand[j],
    )
    model.P = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: capacity[i][j],
    )
    model.C = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: cost[i][j],
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def availability_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) <= mdl.A[i]

    model.availability_limits = pyo.Constraint(
        model.I, rule=availability_rule
    )

    def demand_rule(mdl, j):
        return sum(
            mdl.P[i, j] * mdl.x[i, j] for i in mdl.I
        ) >= mdl.D[j]

    model.demand_requirements = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.C[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}