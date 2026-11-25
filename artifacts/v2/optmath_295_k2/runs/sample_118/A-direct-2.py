import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    capacity = params["capacity"]

    employees = list(range(4))
    projects = list(range(6))

    model = pyo.ConcreteModel()

    model.employee_set = pyo.Set(initialize=employees)
    model.project_set = pyo.Set(initialize=projects)
    model.assignment_set = pyo.Set(
        dimen=2, initialize=[(i, j) for i in employees for j in projects]
    )

    model.assignment = pyo.Var(
        model.assignment_set, domain=pyo.NonNegativeReals
    )

    def obj_rule(m):
        return sum(
            assignment_cost[i][j] * m.assignment[i, j]
            for i in employees
            for j in projects
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return (
            sum(m.assignment[i, j] for j in projects)
            <= employee_availability[i]
        )

    model.availability_con = pyo.Constraint(
        model.employee_set, rule=avail_rule
    )

    def demand_rule(m, j):
        return (
            sum(m.assignment[i, j] for i in employees)
            == project_demand[j]
        )

    model.demand_con = pyo.Constraint(model.project_set, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.assignment[i, j] <= capacity[i][j]

    model.capacity_con = pyo.Constraint(model.assignment_set, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}