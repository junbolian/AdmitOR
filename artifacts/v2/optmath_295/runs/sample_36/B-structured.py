# IR: {"sets":{"people":"0..7","projects":"0..6"},"params":["total_capacity","project_demand","cost_min","cost_max","assignment_limit_min","assignment_limit_max"],"coefficient_completion":{"assumption":"Pair-specific costs and limits are unspecified; generate reproducible continuous coefficients within the supplied bounds.","generator":"random.Random(0)","order":"All costs first, then all limits; each in people-major, projects-minor order.","cost[i,j]":"uniform(cost_min,cost_max)","limit[i,j]":"uniform(assignment_limit_min,assignment_limit_max)"},"variables":{"assignment[i,j]":"NonNegativeReals"},"constraints":["sum_j assignment[i,j] == total_capacity[i] for every person i","sum_i assignment[i,j] == project_demand[j] for every project j","assignment[i,j] <= limit[i,j] for every pair (i,j)","assignment[0,j] == 0 for every project j"],"objective":"minimize sum_(i,j) cost[i,j]*assignment[i,j]"}
#
# The sampling assumption completes the missing assignment-level data.
# Different assignment-level data can produce a different optimal objective.

import random

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    total_capacity = params["total_capacity"]
    project_demand = params["project_demand"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    assignment_limit_min = params["assignment_limit_min"]
    assignment_limit_max = params["assignment_limit_max"]

    if (
        cost_min > cost_max
        or assignment_limit_min > assignment_limit_max
    ):
        return {"objective": None, "status": "invalid_bounds"}

    people = range(8)
    projects = range(7)
    rng = random.Random(0)

    costs = {
        (person, project): rng.uniform(cost_min, cost_max)
        for person in people
        for project in projects
    }
    limits = {
        (person, project): rng.uniform(
            assignment_limit_min, assignment_limit_max
        )
        for person in people
        for project in projects
    }

    model = pyo.ConcreteModel()
    model.people = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 6)

    model.person_capacity = pyo.Param(
        model.people,
        initialize={
            person: total_capacity[person]
            for person in people
        },
        within=pyo.Reals,
    )
    model.required_demand = pyo.Param(
        model.projects,
        initialize={
            project: project_demand[project]
            for project in projects
        },
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.people,
        model.projects,
        initialize=costs,
        within=pyo.Reals,
    )
    model.contribution_limit = pyo.Param(
        model.people,
        model.projects,
        initialize=limits,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.people,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(instance, person):
        return (
            sum(
                instance.assignment[person, project]
                for project in instance.projects
            )
            == instance.person_capacity[person]
        )

    def demand_rule(instance, project):
        return (
            sum(
                instance.assignment[person, project]
                for person in instance.people
            )
            == instance.required_demand[project]
        )

    def contribution_rule(instance, person, project):
        return (
            instance.assignment[person, project]
            <= instance.contribution_limit[person, project]
        )

    def unavailable_rule(instance, project):
        return instance.assignment[0, project] == 0

    model.capacity_balance = pyo.Constraint(
        model.people, rule=capacity_rule
    )
    model.demand_balance = pyo.Constraint(
        model.projects, rule=demand_rule
    )
    model.assignment_ceiling = pyo.Constraint(
        model.people,
        model.projects,
        rule=contribution_rule,
    )
    model.unavailable_person = pyo.Constraint(
        model.projects, rule=unavailable_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[person, project]
            * model.assignment[person, project]
            for person in model.people
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}