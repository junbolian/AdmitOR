# IR: {"sets":{"employees":[0,1,2,3,4],"projects":[0,1,2,3,4]},"params":{"cost":"employees x projects","employee_capacity":"employees","project_demand":"projects","per_project_limit":"employees x projects"},"variables":{"contribution[i,j]":"nonnegative continuous"},"constraints":["sum_j contribution[i,j] == employee_capacity[i] for each employee i","sum_i contribution[i,j] == project_demand[j] for each project j","contribution[i,j] <= per_project_limit[i,j] for each employee-project pair"],"objective":"minimize sum_i sum_j cost[i,j] * contribution[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    per_project_limit = params["per_project_limit"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 4)
    model.projects = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: cost[i][j],
    )
    model.employee_capacity = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_capacity[i],
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_demand[j],
    )
    model.per_project_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: per_project_limit[i][j],
    )

    model.contribution = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_capacity_rule(mdl, i):
        return (
            sum(mdl.contribution[i, j] for j in mdl.projects)
            == mdl.employee_capacity[i]
        )

    model.employee_capacity_constraint = pyo.Constraint(
        model.employees,
        rule=employee_capacity_rule,
    )

    def project_demand_rule(mdl, j):
        return (
            sum(mdl.contribution[i, j] for i in mdl.employees)
            == mdl.project_demand[j]
        )

    model.project_demand_constraint = pyo.Constraint(
        model.projects,
        rule=project_demand_rule,
    )

    def per_project_limit_rule(mdl, i, j):
        return mdl.contribution[i, j] <= mdl.per_project_limit[i, j]

    model.per_project_limit_constraint = pyo.Constraint(
        model.employees,
        model.projects,
        rule=per_project_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.contribution[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}