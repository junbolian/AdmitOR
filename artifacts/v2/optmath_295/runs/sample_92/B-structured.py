# IR: {"sets":{"employees":[0,1,2,3,4],"projects":[0,1,2,3,4]},"params":{"employee_availability":"nonnegative vector indexed by employee","project_requirements":"nonnegative vector indexed by project","assignment_costs":"real matrix indexed by employee, project","assignment_limits":"nonnegative matrix indexed by employee, project"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["sum_j hours[i,j] <= employee_availability[i] for each employee i","sum_i hours[i,j] == project_requirements[j] for each project j","hours[i,j] <= assignment_limits[i,j] for every employee-project pair"],"objective":"minimize sum_i sum_j assignment_costs[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 4)
    model.projects = pyo.RangeSet(0, 4)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_availability[i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_requirements[j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_costs = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_costs[i][j],
        within=pyo.Reals,
    )
    model.assignment_limits = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_limits[i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.employee_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.employees,
        rule=availability_rule,
    )

    def requirement_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.project_requirements[j]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects,
        rule=requirement_rule,
    )

    def assignment_limit_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.assignment_limits[i, j]

    model.assignment_limit_constraints = pyo.Constraint(
        model.employees,
        model.projects,
        rule=assignment_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_costs[i, j] * model.hours[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        # Leave other unexpected runtime errors visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no solution available"}

    return {"objective": obj_val, "status": "optimal"}