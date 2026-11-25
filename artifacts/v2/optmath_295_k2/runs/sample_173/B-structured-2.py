# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"capacity":"params['capacity'][i]","demand":"params['demand'][j]","min_contributors":"params['min_contributors']","min_delivery":"params['min_delivery'][i]","cost":"params['cost'][i][j]"},"variables":{"energy[i,j]":"NonNegativeReals","contributes[i,j]":"Binary"},"constraints":["sum_j energy[i,j] <= capacity[i] for each i","sum_i energy[i,j] >= demand[j] for each j","sum_i contributes[i,j] >= min_contributors for each j","energy[i,j] >= min_delivery[i]*contributes[i,j] for each i,j","energy[i,j] <= capacity[i]*contributes[i,j] for each i,j"],"objective":"minimize sum_i sum_j cost[i,j]*energy[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.J = pyo.RangeSet(0, 4)

    model.capacity = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["capacity"][i],
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["demand"][j],
    )
    model.min_contributors = pyo.Param(
        initialize=params["min_contributors"],
    )
    model.min_delivery = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["min_delivery"][i],
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["cost"][i][j],
    )

    model.energy = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
    model.contributes = pyo.Var(model.I, model.J, domain=pyo.Binary)

    model.producer_capacity = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.energy[i, j] for j in mdl.J) <= mdl.capacity[i]
        ),
    )
    model.contract_demand = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.energy[i, j] for i in mdl.I) >= mdl.demand[j]
        ),
    )
    model.contributor_requirement = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.contributes[i, j] for i in mdl.I)
            >= mdl.min_contributors
        ),
    )
    model.minimum_delivery = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: (
            mdl.energy[i, j]
            >= mdl.min_delivery[i] * mdl.contributes[i, j]
        ),
    )
    model.contribution_link = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: (
            mdl.energy[i, j]
            <= mdl.capacity[i] * mdl.contributes[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.energy[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}