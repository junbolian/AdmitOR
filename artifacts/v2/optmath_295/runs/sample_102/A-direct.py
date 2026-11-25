import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_people = 8
    num_projects = 8
    people = range(num_people)
    projects = range(num_projects)

    capacity = params["employee_capacity"]
    demand = params["project_demand"]
    cost = params["cost_matrix"]
    limit = params["assignment_limit"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(people))
    model.J = pyo.Set(initialize=list(projects))

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.P for j in mdl.J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def person_cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) <= capacity[i]

    model.person_cap = pyo.Constraint(model.P, rule=person_cap_rule)

    def project_demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.P) == demand[j]

    model.project_demand = pyo.Constraint(model.J, rule=project_demand_rule)

    def assignment_limit_rule(mdl, i, j):
        return mdl.x[i, j] <= limit[i][j]

    model.assignment_limit = pyo.Constraint(model.P, model.J, rule=assignment_limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}