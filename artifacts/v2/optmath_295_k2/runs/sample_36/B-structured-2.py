# IR: {"sets":{"persons":"0..7","projects":"0..6"},"params":{"individual_total_capacity":"persons","project_demand":"projects","assignment_cost":"persons x projects","max_contribution_per_project":"persons x projects"},"variables":{"allocation[i,j]":"continuous, nonnegative"},"constraints":["sum_j allocation[i,j] = individual_total_capacity[i] for each person i","sum_i allocation[i,j] = project_demand[j] for each project j","allocation[i,j] <= max_contribution_per_project[i,j] for each person i and project j"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * allocation[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.persons = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 6)

    model.individual_total_capacity = pyo.Param(
        model.persons,
        initialize=lambda model, person: params["individual_total_capacity"][person],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda model, project: params["project_demand"][project],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda model, person, project: params["assignment_cost"][person][project],
        within=pyo.Reals,
    )
    model.max_contribution_per_project = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda model, person, project: params[
            "max_contribution_per_project"
        ][person][project],
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

    model.capacity_balance = pyo.Constraint(
        model.persons,
        rule=capacity_rule,
    )

    def demand_rule(model, project):
        return (
            sum(model.allocation[person, project] for person in model.persons)
            == model.project_demand[project]
        )

    model.demand_balance = pyo.Constraint(
        model.projects,
        rule=demand_rule,
    )

    def contribution_rule(model, person, project):
        return (
            model.allocation[person, project]
            <= model.max_contribution_per_project[person, project]
        )

    model.contribution_limits = pyo.Constraint(
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