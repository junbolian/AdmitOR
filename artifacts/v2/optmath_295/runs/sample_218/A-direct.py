import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    n_consultants = 7
    n_projects = 6

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_consultants - 1)
    model.J = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            assignment_cost[i][j] * m.x[i, j]
            for i in range(n_consultants)
            for j in range(n_projects)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def availability_rule(m, i):
        return sum(m.x[i, j] for j in range(n_projects)) <= consultant_availability[i]

    model.availability_con = pyo.Constraint(model.I, rule=availability_rule)

    def requirement_rule(m, j):
        return sum(m.x[i, j] for i in range(n_consultants)) == project_requirement[j]

    model.requirement_con = pyo.Constraint(model.J, rule=requirement_rule)

    def limit_rule(m, i, j):
        return m.x[i, j] <= assignment_limit[i][j]

    model.limit_con = pyo.Constraint(model.I, model.J, rule=limit_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}