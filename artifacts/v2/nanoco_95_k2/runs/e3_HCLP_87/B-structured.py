# IR: {"sets":{"N":"1..20","S":"1..14","A1":"{(i,j): distance[i,j] <= R1}","A2":"{(i,j): distance[i,j] <= R2}"},"params":{"construction_cost":"params['construction_cost'], indexed by S","demand":"params['demand'], indexed by N; informational priority, not an additional bonus multiplier","bonus":"params['bonus'], indexed by N","R1":"params['R1']","R2":"params['R2']","distance":"fixed supplied 20-by-14 distance matrix"},"variables":{"opened[j]":"binary, j in S","ultrafast[i]":"binary, i in N"},"constraints":["safe_coverage[i]: sum(opened[j] for (i,j) in A1) >= 1","access_upper[i]: ultrafast[i] <= sum(opened[j] for (i,j) in A2)","access_lower[i,j]: ultrafast[i] >= opened[j] for (i,j) in A2"],"objective":"minimize sum(construction_cost[j]*opened[j]) - sum(bonus[i]*ultrafast[i])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = (
        (7, 50, 103, 64, 66, 55, 25, 92, 10, 48, 48, 47, 78, 36),
        (43, 18, 70, 18, 57, 43, 27, 96, 48, 39, 28, 72, 81, 60),
        (68, 62, 69, 96, 27, 37, 63, 20, 62, 40, 51, 32, 7, 37),
        (18, 38, 84, 63, 43, 33, 19, 70, 14, 27, 31, 30, 55, 17),
        (107, 64, 20, 74, 64, 65, 89, 92, 108, 70, 66, 107, 84, 100),
        (66, 61, 70, 95, 27, 37, 62, 22, 61, 39, 51, 30, 9, 35),
        (58, 20, 39, 49, 25, 17, 41, 65, 58, 21, 17, 60, 51, 52),
        (94, 80, 67, 114, 42, 56, 87, 9, 89, 61, 71, 58, 20, 63),
        (6, 49, 102, 62, 66, 54, 24, 93, 11, 47, 47, 48, 79, 37),
        (48, 27, 52, 61, 13, 3, 35, 51, 46, 8, 17, 41, 36, 33),
        (53, 67, 93, 98, 47, 48, 56, 46, 45, 47, 57, 8, 37, 21),
        (83, 78, 78, 112, 41, 53, 79, 9, 77, 57, 68, 43, 15, 51),
        (54, 10, 48, 34, 39, 27, 35, 80, 56, 27, 17, 67, 65, 57),
        (72, 31, 50, 28, 59, 50, 54, 99, 76, 50, 40, 91, 86, 80),
        (43, 10, 63, 25, 48, 34, 25, 88, 47, 31, 20, 67, 73, 55),
        (30, 16, 72, 34, 47, 33, 12, 85, 34, 27, 19, 57, 69, 44),
        (55, 12, 48, 32, 42, 30, 37, 82, 58, 30, 20, 70, 68, 60),
        (100, 57, 15, 70, 57, 58, 82, 86, 101, 63, 59, 100, 78, 93),
        (28, 17, 69, 44, 38, 24, 11, 74, 29, 17, 14, 46, 59, 34),
        (75, 74, 81, 108, 40, 50, 72, 18, 68, 52, 63, 33, 17, 42),
    )

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(1, 20)
    model.S = pyo.RangeSet(1, 14)

    model.construction_cost = pyo.Param(
        model.S,
        initialize={
            j: params["construction_cost"][j - 1]
            for j in model.S
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.N,
        initialize={i: params["demand"][i - 1] for i in model.N},
        within=pyo.Reals,
    )
    model.bonus = pyo.Param(
        model.N,
        initialize={i: params["bonus"][i - 1] for i in model.N},
        within=pyo.Reals,
    )
    model.R1 = pyo.Param(initialize=params["R1"], within=pyo.Reals)
    model.R2 = pyo.Param(initialize=params["R2"], within=pyo.Reals)
    model.distance = pyo.Param(
        model.N,
        model.S,
        initialize={
            (i, j): distances[i - 1][j - 1]
            for i in model.N
            for j in model.S
        },
        within=pyo.NonNegativeReals,
    )

    safe_sites = {
        i: tuple(
            j for j in model.S
            if pyo.value(model.distance[i, j]) <= pyo.value(model.R1)
        )
        for i in model.N
    }
    convenience_sites = {
        i: tuple(
            j for j in model.S
            if pyo.value(model.distance[i, j]) <= pyo.value(model.R2)
        )
        for i in model.N
    }

    model.A1 = pyo.Set(
        dimen=2,
        within=model.N * model.S,
        initialize=[
            (i, j) for i in model.N for j in safe_sites[i]
        ],
    )
    model.A2 = pyo.Set(
        dimen=2,
        within=model.N * model.S,
        initialize=[
            (i, j) for i in model.N for j in convenience_sites[i]
        ],
    )

    model.opened = pyo.Var(model.S, domain=pyo.Binary)
    model.ultrafast = pyo.Var(model.N, domain=pyo.Binary)

    def safe_coverage_rule(instance, i):
        if not safe_sites[i]:
            return pyo.Constraint.Infeasible
        return pyo.quicksum(
            instance.opened[j] for j in safe_sites[i]
        ) >= 1

    model.safe_coverage = pyo.Constraint(
        model.N, rule=safe_coverage_rule
    )

    def access_upper_rule(instance, i):
        return instance.ultrafast[i] <= pyo.quicksum(
            instance.opened[j] for j in convenience_sites[i]
        )

    model.access_upper = pyo.Constraint(
        model.N, rule=access_upper_rule
    )

    def access_lower_rule(instance, i, j):
        return instance.ultrafast[i] >= instance.opened[j]

    model.access_lower = pyo.Constraint(
        model.A2, rule=access_lower_rule
    )

    model.net_cost = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.construction_cost[j] * model.opened[j]
                for j in model.S
            )
            - pyo.quicksum(
                model.bonus[i] * model.ultrafast[i]
                for i in model.N
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.net_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}