# IR: {"sets":{"V":"0,...,7"},"params":{"x_coords":"village x-coordinates","y_coords":"village y-coordinates","student_counts":"students per village","num_schools":"required number of schools","distance[i,j]":"Euclidean distance derived from x_coords and y_coords"},"variables":{"school[j]":"binary","assign[i,j]":"binary"},"constraints":["sum_j school[j] = num_schools","sum_j assign[i,j] = 1 for each i","assign[i,j] <= school[j] for each i,j"],"objective":"minimize sum_i sum_j student_counts[i] * distance[i,j] * assign[i,j]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    student_counts = params["student_counts"]
    num_schools = params["num_schools"]

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, 7)

    model.distance = pyo.Param(
        model.V,
        model.V,
        initialize={
            (i, j): math.hypot(
                x_coords[i] - x_coords[j],
                y_coords[i] - y_coords[j],
            )
            for i in model.V
            for j in model.V
        },
        within=pyo.NonNegativeReals,
    )
    model.students = pyo.Param(
        model.V,
        initialize={i: student_counts[i] for i in model.V},
        within=pyo.NonNegativeReals,
    )
    model.required_schools = pyo.Param(
        initialize=num_schools,
        within=pyo.NonNegativeIntegers,
    )

    model.school = pyo.Var(model.V, domain=pyo.Binary)
    model.assign = pyo.Var(model.V, model.V, domain=pyo.Binary)

    model.school_count = pyo.Constraint(
        expr=sum(model.school[j] for j in model.V)
        == model.required_schools
    )

    def assignment_rule(instance, i):
        return sum(instance.assign[i, j] for j in instance.V) == 1

    model.assignment_constraints = pyo.Constraint(
        model.V, rule=assignment_rule
    )

    def open_school_rule(instance, i, j):
        return instance.assign[i, j] <= instance.school[j]

    model.open_school_constraints = pyo.Constraint(
        model.V, model.V, rule=open_school_rule
    )

    model.total_walking_distance = pyo.Objective(
        expr=sum(
            model.students[i] * model.distance[i, j] * model.assign[i, j]
            for i in model.V
            for j in model.V
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_walking_distance))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solve_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}