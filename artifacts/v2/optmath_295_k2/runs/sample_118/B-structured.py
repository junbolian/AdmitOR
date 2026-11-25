# IR: {"sets":{"E":[0,1,2,3],"P":[0,1,2,3,4,5]},"params":{"employee_availability":"a[e]","project_demand":"d[p]","assignment_cost":"c[e,p]","capacity":"u[e,p]"},"variables":{"x[e,p]":"continuous, nonnegative"},"constraints":["sum(p in P, x[e,p]) <= a[e] for e in E","sum(e in E, x[e,p]) == d[p] for p in P","x[e,p] <= u[e,p] for e in E, p in P"],"objective":"minimize sum(e in E, p in P, c[e,p]*x[e,p])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 5)

    model.availability_data = pyo.Param(
        model.employees,
        initialize=lambda mdl, employee: employee_availability[employee],
        within=pyo.NonNegativeReals,
    )
    model.demand_data = pyo.Param(
        model.projects,
        initialize=lambda mdl, project: project_demand[project],
        within=pyo.NonNegativeReals,
    )
    model.cost_data = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, employee, project: assignment_cost[employee][project],
        within=pyo.Reals,
    )
    model.capacity_data = pyo.Param(
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

    def employee_limit_rule(mdl, employee):
        return (
            sum(mdl.assigned_time[employee, project] for project in mdl.projects)
            <= mdl.availability_data[employee]
        )

    model.employee_limits = pyo.Constraint(
        model.employees,
        rule=employee_limit_rule,
    )

    def project_requirement_rule(mdl, project):
        return (
            sum(mdl.assigned_time[employee, project] for employee in mdl.employees)
            == mdl.demand_data[project]
        )

    model.project_requirements = pyo.Constraint(
        model.projects,
        rule=project_requirement_rule,
    )

    def assignment_limit_rule(mdl, employee, project):
        return (
            mdl.assigned_time[employee, project]
            <= mdl.capacity_data[employee, project]
        )

    model.assignment_limits = pyo.Constraint(
        model.employees,
        model.projects,
        rule=assignment_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_data[employee, project]
            * model.assigned_time[employee, project]
            for employee in model.employees
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}