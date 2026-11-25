import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    member_capacity = params["member_capacity"]
    project_requirement = params["project_requirement"]

    # Structural constants
    members = list(range(6))
    projects = list(range(8))

    # Cost matrix: cost[i][j] for member i, project j
    cost_data = [
        [25, 32, 41, 30, 36, 43, 52, 27],
        [29, 27, 38, 48, 25, 35, 40, 31],
        [34, 40, 22, 36, 47, 29, 38, 45],
        [26, 31, 35, 24, 41, 38, 32, 44],
        [37, 23, 30, 39, 28, 46, 33, 36],
        [39, 33, 35, 28, 38, 25, 42, 29],
    ]

    # Per-assignment upper bound: max_hours[i][j]
    max_hours_data = [
        [10, 7, 5, 8, 6, 9, 7, 5],
        [8, 6, 7, 5, 9, 6, 8, 4],
        [7, 8, 6, 9, 5, 7, 6, 8],
        [9, 5, 8, 6, 7, 5, 9, 6],
        [6, 9, 5, 7, 8, 6, 5, 7],
        [5, 7, 9, 6, 6, 8, 7, 9],
    ]

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=members)
    model.P = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.M, model.P, domain=pyo.NonNegativeReals)

    # Capacity per member per project
    model.x_upper = pyo.Constraint(
        model.M, model.P,
        rule=lambda m_, i, j: model.x[i, j] <= max_hours_data[i][j]
    )

    # Member total time must match available time
    model.member_balance = pyo.Constraint(
        model.M,
        rule=lambda m_, i: sum(model.x[i, j] for j in model.P) == member_capacity[i]
    )

    # Project effort must match requirement
    model.project_balance = pyo.Constraint(
        model.P,
        rule=lambda m_, j: sum(model.x[i, j] for i in model.M) == project_requirement[j]
    )

    model.obj = pyo.Objective(
        expr=sum(cost_data[i][j] * model.x[i, j] for i in model.M for j in model.P),
        sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}