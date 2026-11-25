# IR: {"sets":{"I":"communities 0..27","J":"candidate depots 0..9","A1[i]":"{j: distance[i][j] <= R1}","A2[i]":"{j: distance[i][j] <= R2}"},"params":{"establishment_cost":"params['establishment_cost'], length 10","efficiency_gain":"params['efficiency_gain'], length 28; gain per eligible community","R1":"params['R1']","R2":"params['R2']","demand":"params['demand'], length 28; informational, no capacity constraints or demand weighting","distance":"fixed supplied 28x10 distance matrix"},"variables":{"open_depot[j]":"binary","rapid_eligible[i]":"binary"},"constraints":["For every i: sum(open_depot[j] for j in A1[i]) >= 1.","For every i: rapid_eligible[i] <= sum(open_depot[j] for j in A2[i]).","For every i and j in A2[i]: rapid_eligible[i] >= open_depot[j]."],"objective":"minimize sum(establishment_cost[j]*open_depot[j] for j in J) - sum(efficiency_gain[i]*rapid_eligible[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_cost = list(params["establishment_cost"])
    efficiency_gain = list(params["efficiency_gain"])
    R1 = float(params["R1"])
    R2 = float(params["R2"])
    demand = list(params["demand"])

    if len(establishment_cost) != 10:
        raise ValueError("establishment_cost must contain exactly 10 values.")
    if len(efficiency_gain) != 28:
        raise ValueError("efficiency_gain must contain exactly 28 values.")
    if len(demand) != 28:
        raise ValueError("demand must contain exactly 28 values.")

    distances = (
        (11, 16, 21, 49, 78, 100, 64, 38, 41, 64),
        (29, 33, 16, 52, 61, 95, 60, 67, 62, 54),
        (64, 43, 71, 40, 81, 79, 53, 22, 13, 63),
        (62, 37, 65, 23, 64, 63, 35, 34, 14, 45),
        (70, 52, 63, 29, 13, 45, 20, 77, 60, 8),
        (56, 53, 43, 55, 43, 84, 55, 87, 77, 45),
        (15, 35, 8, 64, 81, 112, 75, 63, 64, 72),
        (60, 35, 59, 5, 45, 51, 18, 47, 28, 27),
        (32, 17, 41, 42, 79, 92, 58, 18, 22, 62),
        (22, 22, 13, 45, 61, 91, 55, 56, 51, 51),
        (25, 10, 33, 40, 74, 91, 55, 26, 27, 58),
        (73, 61, 62, 48, 20, 62, 41, 91, 77, 29),
        (43, 22, 50, 34, 74, 82, 50, 16, 9, 56),
        (4, 26, 10, 58, 81, 108, 71, 51, 54, 69),
        (46, 26, 42, 17, 39, 63, 26, 53, 39, 24),
        (62, 62, 49, 65, 50, 91, 65, 96, 86, 54),
        (49, 48, 36, 54, 48, 87, 56, 82, 73, 47),
        (6, 20, 16, 53, 79, 104, 67, 43, 46, 66),
        (14, 32, 4, 60, 77, 108, 72, 61, 62, 68),
        (75, 51, 73, 18, 35, 34, 8, 64, 44, 19),
        (33, 25, 44, 51, 88, 102, 67, 16, 28, 72),
        (56, 34, 62, 33, 74, 76, 47, 21, 4, 56),
        (106, 83, 101, 50, 37, 5, 35, 96, 76, 37),
        (23, 9, 30, 40, 74, 92, 56, 28, 29, 58),
        (55, 37, 64, 44, 86, 88, 59, 10, 13, 67),
        (23, 34, 9, 57, 69, 102, 67, 66, 64, 62),
        (34, 29, 24, 40, 50, 82, 47, 63, 55, 42),
        (24, 7, 30, 38, 72, 90, 54, 29, 28, 56),
    )

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 27)
    model.J = pyo.RangeSet(0, 9)

    model.establishment_cost = pyo.Param(
        model.J,
        initialize={j: establishment_cost[j] for j in range(10)},
        within=pyo.NonNegativeReals,
    )
    model.efficiency_gain = pyo.Param(
        model.I,
        initialize={i: efficiency_gain[i] for i in range(28)},
        within=pyo.Reals,
    )
    model.R1 = pyo.Param(initialize=R1, within=pyo.NonNegativeReals)
    model.R2 = pyo.Param(initialize=R2, within=pyo.NonNegativeReals)
    model.demand = pyo.Param(
        model.I,
        initialize={i: demand[i] for i in range(28)},
        within=pyo.NonNegativeReals,
    )
    model.distance = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): distances[i][j]
            for i in range(28)
            for j in range(10)
        },
        within=pyo.NonNegativeReals,
    )

    model.A1 = pyo.Set(
        model.I,
        within=model.J,
        initialize={
            i: [j for j in range(10) if distances[i][j] <= R1]
            for i in range(28)
        },
    )
    model.A2 = pyo.Set(
        model.I,
        within=model.J,
        initialize={
            i: [j for j in range(10) if distances[i][j] <= R2]
            for i in range(28)
        },
    )
    model.rapid_pairs = pyo.Set(
        dimen=2,
        within=model.I * model.J,
        initialize=[
            (i, j)
            for i in range(28)
            for j in range(10)
            if distances[i][j] <= R2
        ],
    )

    model.open_depot = pyo.Var(model.J, domain=pyo.Binary)
    model.rapid_eligible = pyo.Var(model.I, domain=pyo.Binary)

    def coverage_rule(instance, i):
        if len(instance.A1[i]) == 0:
            return pyo.Constraint.Infeasible
        return sum(
            instance.open_depot[j] for j in instance.A1[i]
        ) >= 1

    model.coverage = pyo.Constraint(model.I, rule=coverage_rule)

    def rapid_upper_rule(instance, i):
        return instance.rapid_eligible[i] <= sum(
            instance.open_depot[j] for j in instance.A2[i]
        )

    model.rapid_upper = pyo.Constraint(model.I, rule=rapid_upper_rule)

    def rapid_lower_rule(instance, i, j):
        return instance.rapid_eligible[i] >= instance.open_depot[j]

    model.rapid_lower = pyo.Constraint(
        model.rapid_pairs,
        rule=rapid_lower_rule,
    )

    model.net_cost = pyo.Objective(
        expr=sum(
            model.establishment_cost[j] * model.open_depot[j]
            for j in model.J
        )
        - sum(
            model.efficiency_gain[i] * model.rapid_eligible[i]
            for i in model.I
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.net_cost))
    except (ValueError, TypeError):
        reason = "solve_failed" if solve_failed else "objective_unavailable"
        return {"objective": None, "status": reason}

    return {"objective": obj_val, "status": "optimal"}