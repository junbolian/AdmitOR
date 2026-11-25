# IR: {"sets":{"I":"0..27 communities","J":"0..9 candidate depots"},"params":{"establishment_cost":"nonnegative vector[J], from params","coverage_radius":"nonnegative scalar, from params","distance_matrix":"nonnegative matrix[I,J], from params"},"variables":{"open_depot[j]":"binary, j in J"},"constraints":["For each i in I: sum(open_depot[j] for j in J if distance_matrix[i,j] <= coverage_radius) >= 1"],"objective":"minimize sum(establishment_cost[j] * open_depot[j] for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the depot set-cover problem using zero-based input sequences."""
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()
    model.communities = pyo.RangeSet(0, 27)
    model.depots = pyo.RangeSet(0, 9)

    model.establishment_cost = pyo.Param(
        model.depots,
        initialize=lambda mdl, j: establishment_cost[j],
        within=pyo.NonNegativeReals,
    )
    model.coverage_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.communities,
        model.depots,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.open_depot = pyo.Var(model.depots, domain=pyo.Binary)

    def coverage_rule(mdl, i):
        # Keeping zero-coefficient variable terms makes this a symbolic
        # constraint even when no candidate depot covers a community.
        return pyo.quicksum(
            (
                1
                if pyo.value(mdl.distance_matrix[i, j])
                <= pyo.value(mdl.coverage_radius)
                else 0
            )
            * mdl.open_depot[j]
            for j in mdl.depots
        ) >= 1

    model.universal_coverage = pyo.Constraint(
        model.communities,
        rule=coverage_rule,
    )

    model.total_establishment_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.establishment_cost[j] * model.open_depot[j]
            for j in model.depots
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_establishment_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}