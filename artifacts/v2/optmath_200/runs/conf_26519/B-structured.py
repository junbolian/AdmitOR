# IR: {"sets":{"employees":"0..5","projects":"0..6"},"params":{"employee_capacity":"nonnegative vector indexed by employee","project_demand":"nonnegative vector indexed by project","allocation_limit":"nonnegative matrix indexed by employee, project","cost_per_hour":"real matrix indexed by employee, project"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["sum_j hours[i,j] <= employee_capacity[i] for each employee i","sum_i hours[i,j] == project_demand[j] for each project j","hours[i,j] <= allocation_limit[i,j] for each employee i and project j"],"objective":"minimize sum_i sum_j cost_per_hour[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Read vectors as params[key][i] and matrices as params[key][i][j]."""
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    allocation_limit = params["allocation_limit"]
    cost_per_hour = params["cost_per_hour"]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 6)

    model.employee_capacity = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_demand[j],
        within=pyo.NonNegativeReals,
    )
    model.allocation_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: allocation_limit[i][j],
        within=pyo.NonNegativeReals,
    )
    model.cost_per_hour = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: cost_per_hour[i][j],
        within=pyo.Reals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.capacity_constraints = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.employee_capacity[i]
        ),
    )
    model.demand_constraints = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.project_demand[j]
        ),
    )
    model.allocation_constraints = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.allocation_limit[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_per_hour[i, j] * model.hours[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by objective retrieval below.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solver_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}