import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_capacity = params["consultant_capacity"]
    project_requirement = params["project_requirement"]
    cost = params["cost"]
    assignment_capacity = params["assignment_capacity"]

    n_consultants = len(consultant_capacity)
    n_projects = len(project_requirement)

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, n_consultants - 1)
    model.P = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.C, model.P, domain=pyo.NonNegativeReals)

    def proj_rule(m, j):
        return sum(m.x[i, j] for i in m.C) == project_requirement[j]
    model.proj_con = pyo.Constraint(model.P, rule=proj_rule)

    def cons_rule(m, i):
        return sum(m.x[i, j] for j in m.P) <= consultant_capacity[i]
    model.cons_con = pyo.Constraint(model.C, rule=cons_rule)

    model.x_ub = pyo.Constraint(
        model.C, model.P,
        rule=lambda m, i, j: m.x[i, j] <= assignment_capacity[i][j]
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.C for j in model.P),
        sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}