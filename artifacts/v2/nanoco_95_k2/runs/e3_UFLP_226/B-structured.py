# IR: {"sets":{"I":"0..18","J":"0..4"},"params":{"investment_cost":"investment_cost[j], j in J, from params","distance_matrix":"distance_matrix[i][j], (i,j) in I x J, from params"},"variables":{"open_site[j]":"binary, j in J","assign[i,j]":"binary, (i,j) in I x J"},"constraints":["sum(assign[i,j] for j in J) == 1 for each i in I","assign[i,j] <= open_site[j] for each (i,j) in I x J"],"objective":"minimize sum(investment_cost[j]*open_site[j] for j in J) + sum(distance_matrix[i][j]*assign[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investment_cost = params["investment_cost"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 18)
    model.J = pyo.RangeSet(0, 4)

    model.investment_cost = pyo.Param(
        model.J,
        initialize=lambda instance, j: investment_cost[j],
        within=pyo.Reals,
    )
    model.travel_distance = pyo.Param(
        model.I,
        model.J,
        initialize=lambda instance, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )

    model.open_site = pyo.Var(model.J, domain=pyo.Binary)
    model.assign = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def exactly_one_station(instance, i):
        return sum(instance.assign[i, j] for j in instance.J) == 1

    model.assignment_requirement = pyo.Constraint(
        model.I,
        rule=exactly_one_station,
    )

    def operational_station_required(instance, i, j):
        return instance.assign[i, j] <= instance.open_site[j]

    model.operational_requirement = pyo.Constraint(
        model.I,
        model.J,
        rule=operational_station_required,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.investment_cost[j] * model.open_site[j]
            for j in model.J
        )
        + sum(
            model.travel_distance[i, j] * model.assign[i, j]
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