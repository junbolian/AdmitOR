import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    allocation_limit = params["allocation_limit"]
    cost_per_hour = params["cost_per_hour"]

    num_employees = len(employee_capacity)
    num_projects = len(project_demand)

    employees = list(range(num_employees))
    projects = list(range(num_projects))

    model = pyo.ConcreteModel()

    model.EMP = pyo.Set(initialize=employees)
    model.PROJ = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.EMP, model.PROJ, domain=pyo.NonNegativeReals)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.PROJ) <= employee_capacity[i]
    model.cap = pyo.Constraint(model.EMP, rule=cap_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.EMP) == project_demand[j]
    model.demand = pyo.Constraint(model.PROJ, rule=demand_rule)

    def limit_rule(m, i, j):
        return m.x[i, j] <= allocation_limit[i][j]
    model.limit = pyo.Constraint(model.EMP, model.PROJ, rule=limit_rule)

    def obj_rule(m):
        return sum(cost_per_hour[i][j] * m.x[i, j] for i in m.EMP for j in m.PROJ)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}