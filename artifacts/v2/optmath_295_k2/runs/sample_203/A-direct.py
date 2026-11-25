import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_consultants = len(consultant_hours)
    n_projects = len(project_hours)

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, n_consultants - 1)
    model.P = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.C, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.C for j in m.P)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def consultant_rule(m, i):
        return sum(m.x[i, j] for j in m.P) == consultant_hours[i]

    model.consultant_con = pyo.Constraint(model.C, rule=consultant_rule)

    def project_rule(m, j):
        return sum(m.x[i, j] for i in m.C) == project_hours[j]

    model.project_con = pyo.Constraint(model.P, rule=project_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.C, model.P, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}