# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4]},"params":{"cost":"real[P,C]","capacity":"nonnegative[P]","demand":"nonnegative[C]","min_contributors":"nonnegative_integer[C]","min_delivery":"nonnegative[P]"},"variables":{"energy[P,C]":"continuous, nonnegative","contributes[P,C]":"binary"},"constraints":["For each i: sum_j energy[i,j] <= capacity[i]","For each j: sum_i energy[i,j] >= demand[j]","For each j: sum_i contributes[i,j] >= min_contributors[j]","For each i,j: energy[i,j] >= min_delivery[i]*contributes[i,j]","For each i,j: energy[i,j] <= capacity[i]*contributes[i,j]"],"objective":"minimize sum_i sum_j cost[i,j]*energy[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 4)
    model.C = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda model, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.P,
        initialize=lambda model, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize=lambda model, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.C,
        initialize=lambda model, j: params["min_contributors"][j],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize=lambda model, i: params["min_delivery"][i],
        within=pyo.NonNegativeReals,
    )

    model.energy = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.contributes = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        model.P,
        rule=lambda model, i: (
            sum(model.energy[i, j] for j in model.C) <= model.capacity[i]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.C,
        rule=lambda model, j: (
            sum(model.energy[i, j] for i in model.P) >= model.demand[j]
        ),
    )
    model.contributor_requirement = pyo.Constraint(
        model.C,
        rule=lambda model, j: (
            sum(model.contributes[i, j] for i in model.P)
            >= model.min_contributors[j]
        ),
    )
    model.minimum_delivery_link = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda model, i, j: (
            model.energy[i, j]
            >= model.min_delivery[i] * model.contributes[i, j]
        ),
    )
    model.maximum_delivery_link = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda model, i, j: (
            model.energy[i, j]
            <= model.capacity[i] * model.contributes[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.energy[i, j]
            for i in model.P
            for j in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}