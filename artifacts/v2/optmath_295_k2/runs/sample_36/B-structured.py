# IR: {"sets":{"persons":"0..7","projects":"0..6"},"params":{"individual_total_capacity":"nonnegative vector[8]","project_demand":"nonnegative vector[7]","assignment_cost":"real matrix[8,7]","max_contribution_per_project":"nonnegative matrix[8,7]"},"variables":{"allocation[i,j]":"continuous, nonnegative"},"constraints":["forall i: sum_j allocation[i,j] == individual_total_capacity[i]","forall j: sum_i allocation[i,j] == project_demand[j]","forall i,j: allocation[i,j] <= max_contribution_per_project[i,j]"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * allocation[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["individual_total_capacity"]
    demands = params["project_demand"]
    costs = params["assignment_cost"]
    contribution_limits = params["max_contribution_per_project"]

    model = pyo.ConcreteModel()
    model.persons = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 6)

    model.individual_total_capacity = pyo.Param(
        model.persons,
        initialize={person: capacities[person] for person in range(8)},
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize={project: demands[project] for project in range(7)},
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.persons,
        model.projects,
        initialize={
            (person, project): costs[person][project]
            for person in range(8)
            for project in range(7)
        },
        within=pyo.Reals,
    )
    model.max_contribution_per_project = pyo.Param(
        model.persons,
        model.projects,
        initialize={
            (person, project): contribution_limits[person][project]
            for person in range(8)
            for project in range(7)
        },
        within=pyo.NonNegativeReals,
    )

    model.allocation = pyo.Var(
        model.persons,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(model, person):
        return (
            sum(model.allocation[person, project] for project in model.projects)
            == model.individual_total_capacity[person]
        )

    model.capacity_constraints = pyo.Constraint(
        model.persons, rule=capacity_rule
    )

    def demand_rule(model, project):
        return (
            sum(model.allocation[person, project] for person in model.persons)
            == model.project_demand[project]
        )

    model.demand_constraints = pyo.Constraint(
        model.projects, rule=demand_rule
    )

    def contribution_rule(model, person, project):
        return (
            model.allocation[person, project]
            <= model.max_contribution_per_project[person, project]
        )

    model.contribution_constraints = pyo.Constraint(
        model.persons,
        model.projects,
        rule=contribution_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[person, project]
            * model.allocation[person, project]
            for person in model.persons
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}