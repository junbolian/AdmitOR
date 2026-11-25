# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4,5,6]},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","cost":"cost[i,j] from params['cost']","limit":"limit[i,j] from params['limit']"},"variables":{"x[i,j]":"continuous nonnegative"},"constraints":["sum(j in J, x[i,j]) <= supply[i] for each i in I","sum(i in I, x[i,j]) == demand[j] for each j in J","x[i,j] <= limit[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, cost[i,j] * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 4)
    model.J = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.I,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.limit = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: limit[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.supply_constraints = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.J) <= mdl.supply[i]
        ),
    )
    model.demand_constraints = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.I) == mdl.demand[j]
        ),
    )
    model.transport_constraints = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.limit[i, j],
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}