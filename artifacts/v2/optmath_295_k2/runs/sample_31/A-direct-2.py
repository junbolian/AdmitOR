import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_supply = params["employee_supply"]
    project_demand = params["project_demand"]
    cost = params["cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = len(employee_supply)
    num_projects = len(project_demand)

    employees = list(range(num_employees))
    projects = list(range(num_projects))

    model = pyo.ConcreteModel()

    model.employees = pyo.Set(initialize=employees)
    model.projects = pyo.Set(initialize=projects)
    model.pairs = pyo.Set(
        initialize=[(i, j) for i in employees for j in projects],
        dimen=2,
    )

    model.hours = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)

    model.employee_supply_con = pyo.Constraint(
        model.employees,
        rule=lambda model, i: sum(model.hours[i, j] for j in model.projects)
        == employee_supply[i],
    )
    model.project_demand_con = pyo.Constraint(
        model.projects,
        rule=lambda model, j: sum(model.hours[i, j] for i in model.employees)
        == project_demand[j],
    )
    model.capacity_con = pyo.Constraint(
        model.pairs,
        rule=lambda model, i, j: model.hours[i, j] <= assignment_capacity[i][j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.hours[i, j] for (i, j) in model.pairs),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:80] or "failed"}