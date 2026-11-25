# IR: {"sets":{"I":"1..20 nodes","J":"1..14 sites","A1[i]":"{j in J: D[i,j] <= R1}","A2[i]":"{j in J: D[i,j] <= R2}"},"params":{"construction_cost":"params['construction_cost'], site order","demand":"params['demand'], node order; descriptive priority, not an objective multiplier","bonus":"params['bonus'], node order","R1":"params['R1']","R2":"params['R2']","D":"fixed supplied 20-by-14 distance matrix"},"variables":{"open_site[j]":"binary","ultra_access[i]":"binary"},"constraints":["safe_coverage[i]: sum(open_site[j] for j in A1[i]) >= 1","access_upper[i]: ultra_access[i] <= sum(open_site[j] for j in A2[i])","access_lower[i,j] for j in A2[i]: ultra_access[i] >= open_site[j]"],"objective":"minimize sum(construction_cost[j]*open_site[j] for j in J) - sum(bonus[i]*ultra_access[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    construction_cost = params["construction_cost"]
    demand = params["demand"]
    bonus = params["bonus"]
    safe_radius = float(params["R1"])
    convenience_radius = float(params["R2"])

    if len(construction_cost) != 14:
        raise ValueError("construction_cost must contain exactly 14 values.")
    if len(demand) != 20:
        raise ValueError("demand must contain exactly 20 values.")
    if len(bonus) != 20:
        raise ValueError("bonus must contain exactly 20 values.")

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
    model.nodes = pyo.RangeSet(1, 20)
    model.sites = pyo.RangeSet(1, 14)

    model.construction_cost = pyo.Param(
        model.sites,
        initialize={
            j: float(construction_cost[j - 1]) for j in model.sites
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.nodes,
        initialize={i: float(demand[i - 1]) for i in model.nodes},
        within=pyo.Reals,
    )
    model.bonus = pyo.Param(
        model.nodes,
        initialize={i: float(bonus[i - 1]) for i in model.nodes},
        within=pyo.Reals,
    )
    model.R1 = pyo.Param(initialize=safe_radius, within=pyo.Reals)
    model.R2 = pyo.Param(initialize=convenience_radius, within=pyo.Reals)
    model.distance = pyo.Param(
        model.nodes,
        model.sites,
        initialize={
            (i, j): distances[i - 1][j - 1]
            for i in model.nodes
            for j in model.sites
        },
        within=pyo.NonNegativeReals,
    )

    safe_neighbors = {
        i: tuple(
            j for j in model.sites
            if distances[i - 1][j - 1] <= safe_radius
        )
        for i in model.nodes
    }
    convenience_neighbors = {
        i: tuple(
            j for j in model.sites
            if distances[i - 1][j - 1] <= convenience_radius
        )
        for i in model.nodes
    }

    model.safe_sites = pyo.Set(
        model.nodes, within=model.sites, initialize=safe_neighbors
    )
    model.convenience_sites = pyo.Set(
        model.nodes, within=model.sites, initialize=convenience_neighbors
    )
    model.convenience_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in convenience_neighbors[i]
        ],
    )

    model.open_site = pyo.Var(model.sites, domain=pyo.Binary)
    model.ultra_access = pyo.Var(model.nodes, domain=pyo.Binary)

    def safe_coverage_rule(current_model, i):
        # Tuple form also represents infeasibility when this sum is empty.
        return (
            1,
            pyo.quicksum(
                current_model.open_site[j]
                for j in current_model.safe_sites[i]
            ),
            None,
        )

    model.safe_coverage = pyo.Constraint(
        model.nodes, rule=safe_coverage_rule
    )

    def access_upper_rule(current_model, i):
        return current_model.ultra_access[i] <= pyo.quicksum(
            current_model.open_site[j]
            for j in current_model.convenience_sites[i]
        )

    model.access_upper = pyo.Constraint(
        model.nodes, rule=access_upper_rule
    )

    def access_lower_rule(current_model, i, j):
        return (
            current_model.ultra_access[i] >= current_model.open_site[j]
        )

    model.access_lower = pyo.Constraint(
        model.convenience_pairs, rule=access_lower_rule
    )

    # Bonuses are already specified per node; demand does not multiply them.
    model.net_cost = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.construction_cost[j] * model.open_site[j]
                for j in model.sites
            )
            - pyo.quicksum(
                model.bonus[i] * model.ultra_access[i]
                for i in model.nodes
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.net_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}