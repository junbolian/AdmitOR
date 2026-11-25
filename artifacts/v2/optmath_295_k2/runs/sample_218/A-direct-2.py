import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_cost = params["assignment_cost"]
    assignment_limits = params["assignment_limits"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_requirements)

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, num_consultants - 1)
    model.P = pyo.RangeSet(0, num_projects - 1)

    model.x = pyo.Var(model.C, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            assignment_cost[c][p] * m.x[c, p]
            for c in m.C
            for p in m.P
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def availability_rule(m, c):
        return sum(m.x[c, p] for p in m.P) <= consultant_availability[c]

    model.availability_con = pyo.Constraint(model.C, rule=availability_rule)

    def requirement_rule(m, p):
        return sum(m.x[c, p] for c in m.C) == project_requirements[p]

    model.requirement_con = pyo.Constraint(model.P, rule=requirement_rule)

    def limit_rule(m, c, p):
        return m.x[c, p] <= assignment_limits[c][p]

    model.limit_con = pyo.Constraint(model.C, model.P, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}