import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    cost = params["assignment_cost"]
    limit = params["assignment_limit"]

    num_employees = len(availability)
    num_projects = len(requirements)

    employees = range(num_employees)
    projects = range(num_projects)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(employees, projects, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in employees for j in projects)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in projects) <= availability[i]

    model.avail_con = pyo.Constraint(employees, rule=avail_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in employees) >= requirements[j]

    model.demand_con = pyo.Constraint(projects, rule=demand_rule)

    def limit_rule(m, i, j):
        return m.x[i, j] <= limit[i][j]

    model.limit_con = pyo.Constraint(employees, projects, rule=limit_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}