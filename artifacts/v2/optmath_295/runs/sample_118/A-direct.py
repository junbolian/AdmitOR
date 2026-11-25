import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    pair_capacity = params["pair_capacity"]

    employees = list(range(4))
    projects = list(range(6))

    model = pyo.ConcreteModel()

    model.employee = pyo.Set(initialize=employees)
    model.project = pyo.Set(initialize=projects)
    model.pair = pyo.Set(initialize=[(e, p) for e in employees for p in projects])

    model.x = pyo.Var(model.pair, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(assignment_cost[e][p] * m.x[e, p] for e, p in m.pair)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def availability_rule(m, e):
        return sum(m.x[e, p] for p in m.project) <= employee_availability[e]

    model.availability_con = pyo.Constraint(model.employee, rule=availability_rule)

    def demand_rule(m, p):
        return sum(m.x[e, p] for e in m.employee) == project_demand[p]

    model.demand_con = pyo.Constraint(model.project, rule=demand_rule)

    def capacity_rule(m, e, p):
        return m.x[e, p] <= pair_capacity[e][p]

    model.capacity_con = pyo.Constraint(model.pair, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}