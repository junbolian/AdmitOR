import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirement = params["project_requirement"]
    cost = params["assignment_cost"]
    capacity = params["assignment_capacity"]

    n_emp = len(availability)
    n_proj = len(requirement)

    model = pyo.ConcreteModel()

    model.E = pyo.RangeSet(0, n_emp - 1)
    model.P = pyo.RangeSet(0, n_proj - 1)

    model.x = pyo.Var(model.E, model.P, domain=pyo.NonNegativeReals)

    def emp_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.P) == availability[i]
    model.emp_con = pyo.Constraint(model.E, rule=emp_rule)

    def proj_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.E) == requirement[j]
    model.proj_con = pyo.Constraint(model.P, rule=proj_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]
    model.cap_con = pyo.Constraint(model.E, model.P, rule=cap_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.E for j in mdl.P)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}