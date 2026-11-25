# IR: {"sets":{"consultants":"0..6","projects":"0..5"},"params":{"consultant_availability":"nonnegative vector indexed by consultant","project_requirements":"nonnegative vector indexed by project","assignment_cost":"real matrix indexed by consultant, project","assignment_limits":"nonnegative matrix indexed by consultant, project"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["sum_j hours[i,j] <= consultant_availability[i] for each consultant i","sum_i hours[i,j] == project_requirements[j] for each project j","hours[i,j] <= assignment_limits[i,j] for each consultant-project pair"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed vectors and nested consultant-by-project matrices."""
    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.consultant_availability = pyo.Param(
        model.consultants,
        initialize=lambda model, i: params["consultant_availability"][i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda model, j: params["project_requirements"][j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda model, i, j: params["assignment_cost"][i][j],
        within=pyo.Reals,
    )
    model.assignment_limits = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda model, i, j: params["assignment_limits"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(model, i):
        return (
            sum(model.hours[i, j] for j in model.projects)
            <= model.consultant_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.consultants, rule=availability_rule
    )

    def requirement_rule(model, j):
        return (
            sum(model.hours[i, j] for i in model.consultants)
            == model.project_requirements[j]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects, rule=requirement_rule
    )

    def assignment_limit_rule(model, i, j):
        return model.hours[i, j] <= model.assignment_limits[i, j]

    model.assignment_limit_constraints = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=assignment_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.consultants
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this error when no feasible solution can be loaded.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}