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

    model.employees = pyo.Set(initialize=employees)
    model.projects = pyo.Set(initialize=projects)

    def bounds_rule(model, e, p):
        return (0, capacity[e][p])

    model.x = pyo.Var(model.employees, model.projects, domain=pyo.NonNegativeReals,
                      bounds=bounds_rule)

    def obj_rule(model):
        return sum(assignment_cost[e][p] * model.x[e, p]
                   for e in model.employees for p in model.projects)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def availability_rule(model, e):
        return sum(model.x[e, p] for p in model.projects) <= employee_availability[e]

    model.availability_con = pyo.Constraint(model.employees, rule=availability_rule)

    def demand_rule(model, p):
        return sum(model.x[e, p] for e in model.employees) == project_demand[p]

    model.demand_con = pyo.Constraint(model.projects, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}