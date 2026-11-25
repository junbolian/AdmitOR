# IR: {"sets":{"I":"0..6","J":"0..5"},"params":{"capacity_person":"[I]","demand_project":"[J]","cost_assign":"[I,J]","max_person_project":"[I,J]"},"variables":{"hours[I,J]":"continuous, nonnegative"},"constraints":["sum(hours[i,j] for j in J) <= capacity_person[i] for i in I","sum(hours[i,j] for i in I) == demand_project[j] for j in J","hours[i,j] <= max_person_project[i,j] for i in I, j in J"],"objective":"minimize sum(cost_assign[i,j] * hours[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept vectors indexed by i or j and matrices indexed by [i][j] or [i, j]."""

    def matrix_value(data, i, j):
        if isinstance(data, dict) and (i, j) in data:
            return data[i, j]
        return data[i][j]

    model = pyo.ConcreteModel()
    model.people = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.capacity_person = pyo.Param(
        model.people,
        initialize={i: params["capacity_person"][i] for i in model.people},
    )
    model.demand_project = pyo.Param(
        model.projects,
        initialize={j: params["demand_project"][j] for j in model.projects},
    )
    model.cost_assign = pyo.Param(
        model.people,
        model.projects,
        initialize={
            (i, j): matrix_value(params["cost_assign"], i, j)
            for i in model.people
            for j in model.projects
        },
    )
    model.max_person_project = pyo.Param(
        model.people,
        model.projects,
        initialize={
            (i, j): matrix_value(params["max_person_project"], i, j)
            for i in model.people
            for j in model.projects
        },
    )

    model.hours = pyo.Var(
        model.people, model.projects, domain=pyo.NonNegativeReals
    )

    def capacity_rule(allocation, i):
        return (
            sum(allocation.hours[i, j] for j in allocation.projects)
            <= allocation.capacity_person[i]
        )

    model.person_capacity_limits = pyo.Constraint(
        model.people, rule=capacity_rule
    )

    def demand_rule(allocation, j):
        return (
            sum(allocation.hours[i, j] for i in allocation.people)
            == allocation.demand_project[j]
        )

    model.project_demand_requirements = pyo.Constraint(
        model.projects, rule=demand_rule
    )

    def assignment_limit_rule(allocation, i, j):
        return (
            allocation.hours[i, j]
            <= allocation.max_person_project[i, j]
        )

    model.assignment_limits = pyo.Constraint(
        model.people, model.projects, rule=assignment_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_assign[i, j] * model.hours[i, j]
            for i in model.people
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}