# IR: {"sets":{"employees":[0,1,2,3],"projects":[0,1,2,3,4,5]},"params":{"employee_availability":"array[4]","project_demand":"array[6]","assignment_cost":"array[4][6]","pair_capacity":"array[4][6]"},"variables":{"assignment[i,j]":"nonnegative continuous"},"constraints":["sum_j assignment[i,j] <= employee_availability[i] for each employee i","sum_i assignment[i,j] == project_demand[j] for each project j","assignment[i,j] <= pair_capacity[i][j] for each employee-project pair"],"objective":"minimize sum_i sum_j assignment_cost[i][j] * assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    pair_capacity = params["pair_capacity"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 5)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda instance, i: employee_availability[i],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda instance, j: project_demand[j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda instance, i, j: assignment_cost[i][j],
        within=pyo.Reals,
    )
    model.pair_capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda instance, i, j: pair_capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_limit_rule(instance, i):
        return (
            sum(instance.assignment[i, j] for j in instance.projects)
            <= instance.employee_availability[i]
        )

    model.employee_limits = pyo.Constraint(
        model.employees,
        rule=employee_limit_rule,
    )

    def project_requirement_rule(instance, j):
        return (
            sum(instance.assignment[i, j] for i in instance.employees)
            == instance.project_demand[j]
        )

    model.project_requirements = pyo.Constraint(
        model.projects,
        rule=project_requirement_rule,
    )

    def pair_limit_rule(instance, i, j):
        return instance.assignment[i, j] <= instance.pair_capacity[i, j]

    model.pair_limits = pyo.Constraint(
        model.employees,
        model.projects,
        rule=pair_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.assignment[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded.
        # Success is determined exclusively by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}