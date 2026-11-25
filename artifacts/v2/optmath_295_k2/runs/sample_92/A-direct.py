import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employees = list(range(5))
    projects = list(range(5))

    availability = params["employee_availability"]
    requirement = params["project_requirement"]
    cost = params["assignment_cost"]
    limit = params["assignment_limit"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=employees)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def emp_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= availability[i]

    def proj_rule(m, j):
        return sum(m.x[i, j] for i in m.P) == requirement[j]

    def lim_rule(m, i, j):
        return m.x[i, j] <= limit[i][j]

    model.emp_con = pyo.Constraint(model.P, rule=emp_rule)
    model.proj_con = pyo.Constraint(model.J, rule=proj_rule)
    model.lim_con = pyo.Constraint(model.P, model.J, rule=lim_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.P for j in model.J),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}