# IR: {"sets":{"persons":[0,1,2,3],"projects":[0,1,2,3,4,5]},"params":{"supply":"persons","demand":"projects","upper_limit":"persons x projects","cost":"persons x projects"},"variables":{"x[i,j]":{"type":"continuous","bounds":"0 <= x[i,j] <= upper_limit[i,j]"}},"constraints":["sum(j in projects) x[i,j] == supply[i] for each person i","sum(i in persons) x[i,j] == demand[j] for each project j"],"objective":{"sense":"minimize","expression":"sum(i in persons,j in projects) cost[i,j]*x[i,j]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    upper_limit = params["upper_limit"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.persons = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.persons,
        initialize=lambda mdl, i: supply[i],
    )
    model.demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: demand[j],
    )
    model.upper_limit = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda mdl, i, j: upper_limit[i][j],
    )
    model.cost = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda mdl, i, j: cost[i][j],
    )

    model.x = pyo.Var(
        model.persons,
        model.projects,
        domain=pyo.NonNegativeReals,
        bounds=lambda mdl, i, j: (0, mdl.upper_limit[i, j]),
    )

    model.person_capacity = pyo.Constraint(
        model.persons,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.projects) == mdl.supply[i]
        ),
    )
    model.project_demand = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.persons) == mdl.demand[j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.persons
            for j in model.projects
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