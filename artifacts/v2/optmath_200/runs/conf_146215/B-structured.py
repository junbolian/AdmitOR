# {"sets":{"areas":"0..33","teams":"0..17"},"params":{"activation_costs":"real[18] from params","coverage_matrix":"binary[34][18] from params"},"variables":{"selected[j]":"binary for each team j"},"constraints":["For every area i: sum(coverage_matrix[i][j]*selected[j] for j in teams) >= 1"],"objective":"Minimize sum(activation_costs[j]*selected[j] for j in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_costs = params["activation_costs"]
    coverage_matrix = params["coverage_matrix"]

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 33)
    model.teams = pyo.RangeSet(0, 17)

    model.activation_cost = pyo.Param(
        model.teams,
        initialize=lambda mdl, j: activation_costs[j],
        within=pyo.Reals,
    )
    model.coverage_incidence = pyo.Param(
        model.areas,
        model.teams,
        initialize=lambda mdl, i, j: coverage_matrix[i][j],
        within=pyo.Binary,
    )
    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(mdl, i):
        return sum(
            mdl.coverage_incidence[i, j] * mdl.selected[j]
            for j in mdl.teams
        ) >= 1

    model.area_coverage = pyo.Constraint(model.areas, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[j] * model.selected[j]
            for j in model.teams
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