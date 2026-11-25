import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_consultants = 7
    num_projects = 6
    consultants = list(range(num_consultants))
    projects = list(range(num_projects))

    availability = params["consultant_availability"]
    requirements = params["project_requirements"]
    cost = params["assignment_cost"]
    limits = params["assignment_limits"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=consultants)
    model.P = pyo.Set(initialize=projects)
    model.CP = pyo.Set(initialize=[(c, p) for c in consultants for p in projects])

    model.x = pyo.Var(model.CP, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[c][p] * m.x[c, p] for c in consultants for p in projects)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def avail_rule(m, c):
        return sum(m.x[c, p] for p in projects) <= availability[c]

    model.avail_con = pyo.Constraint(model.C, rule=avail_rule)

    def req_rule(m, p):
        return sum(m.x[c, p] for c in consultants) == requirements[p]

    model.req_con = pyo.Constraint(model.P, rule=req_rule)

    def limit_rule(m, c, p):
        return m.x[c, p] <= limits[c][p]

    model.limit_con = pyo.Constraint(model.CP, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}