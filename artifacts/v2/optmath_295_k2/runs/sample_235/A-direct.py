import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_emp = 6
    num_proj = 6

    availability = params["employee_availability"]
    requirement = params["project_requirement"]
    cost = params["assignment_cost"]
    capacity = params["assignment_capacity"]

    model = pyo.ConcreteModel()

    model.emp = pyo.RangeSet(0, num_emp - 1)
    model.proj = pyo.RangeSet(0, num_proj - 1)

    model.x = pyo.Var(model.emp, model.proj, domain=pyo.NonNegativeReals)

    def emp_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.proj) == availability[i]
    model.emp_con = pyo.Constraint(model.emp, rule=emp_rule)

    def proj_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.emp) == requirement[j]
    model.proj_con = pyo.Constraint(model.proj, rule=proj_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]
    model.cap_con = pyo.Constraint(model.emp, model.proj, rule=cap_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.emp for j in mdl.proj)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}