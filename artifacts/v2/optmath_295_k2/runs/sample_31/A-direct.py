import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_supply = params["employee_supply"]
    project_demand = params["project_demand"]
    cost = params["cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = len(employee_supply)
    num_projects = len(project_demand)

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, num_employees - 1)
    model.projects = pyo.RangeSet(0, num_projects - 1)

    def hours_bounds(m, i, j):
        return (0, assignment_capacity[i][j])

    model.hours = pyo.Var(model.employees, model.projects, bounds=hours_bounds)

    def total_cost_rule(m):
        return sum(cost[i][j] * m.hours[i, j]
                   for i in m.employees for j in m.projects)

    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    def employee_supply_rule(m, i):
        return sum(m.hours[i, j] for j in m.projects) == employee_supply[i]

    model.employee_supply_con = pyo.Constraint(model.employees,
                                               rule=employee_supply_rule)

    def project_demand_rule(m, j):
        return sum(m.hours[i, j] for i in m.employees) == project_demand[j]

    model.project_demand_con = pyo.Constraint(model.projects,
                                              rule=project_demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}