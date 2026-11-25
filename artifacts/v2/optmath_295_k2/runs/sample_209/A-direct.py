import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    person_availability = params["person_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_upper_limit = params["assignment_upper_limit"]

    n_persons = len(person_availability)
    n_projects = len(project_requirement)

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, n_persons - 1)
    model.J = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def cost_rule(mdl):
        return sum(assignment_cost[i][j] * mdl.x[i, j]
                   for i in mdl.P for j in mdl.J)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def person_cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) <= person_availability[i]
    model.person_cap = pyo.Constraint(model.P, rule=person_cap_rule)

    def proj_req_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.P) == project_requirement[j]
    model.proj_req = pyo.Constraint(model.J, rule=proj_req_rule)

    def upper_rule(mdl, i, j):
        return mdl.x[i, j] <= assignment_upper_limit[i][j]
    model.upper_lim = pyo.Constraint(model.P, model.J, rule=upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}