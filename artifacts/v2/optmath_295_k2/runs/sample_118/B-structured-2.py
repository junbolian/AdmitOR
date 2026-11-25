# IR: {"sets":{"employees":[0,1,2,3],"projects":[0,1,2,3,4,5]},"params":{"employee_availability":"nonnegative vector indexed by employee","project_demand":"nonnegative vector indexed by project","assignment_cost":"real matrix indexed by employee, project","capacity":"nonnegative matrix indexed by employee, project"},"variables":{"assigned_time[e,p]":"continuous nonnegative"},"constraints":["For each employee e: sum_p assigned_time[e,p] <= employee_availability[e]","For each project p: sum_e assigned_time[e,p] == project_demand[p]","For each employee e and project p: assigned_time[e,p] <= capacity[e,p]"],"objective":"minimize sum_e sum_p assignment_cost[e,p] * assigned_time[e,p]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using vectors and employee-by-project nested matrices in params."""
    employee_availability = params["employee_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 5)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, employee: employee_availability[employee],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, project: project_demand[project],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, employee, project: assignment_cost[employee][project],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, employee, project: capacity[employee][project],
        within=pyo.NonNegativeReals,
    )

    model.assigned_time = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(mdl, employee):
        return (
            sum(mdl.assigned_time[employee, project] for project in mdl.projects)
            <= mdl.employee_availability[employee]
        )

    model.availability_limits = pyo.Constraint(
        model.employees,
        rule=availability_rule,
    )

    def demand_rule(mdl, project):
        return (
            sum(mdl.assigned_time[employee, project] for employee in mdl.employees)
            == mdl.project_demand[project]
        )

    model.demand_requirements = pyo.Constraint(
        model.projects,
        rule=demand_rule,
    )

    def capacity_rule(mdl, employee, project):
        return (
            mdl.assigned_time[employee, project]
            <= mdl.capacity[employee, project]
        )

    model.assignment_limits = pyo.Constraint(
        model.employees,
        model.projects,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[employee, project]
            * model.assigned_time[employee, project]
            for employee in model.employees
            for project in model.projects
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}