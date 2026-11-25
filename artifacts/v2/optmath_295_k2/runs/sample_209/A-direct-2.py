import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    person_availability = params["person_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_upper_limit = params["assignment_upper_limit"]

    persons = list(range(len(person_availability)))
    projects = list(range(len(project_requirement)))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=persons)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def assignment_limit_rule(model, i, j):
        return model.x[i, j] <= assignment_upper_limit[i][j]
    model.assignment_limit = pyo.Constraint(model.I, model.J, rule=assignment_limit_rule)

    def availability_rule(model, i):
        return sum(model.x[i, j] for j in model.J) <= person_availability[i]
    model.availability = pyo.Constraint(model.I, rule=availability_rule)

    def requirement_rule(model, j):
        return sum(model.x[i, j] for i in model.I) == project_requirement[j]
    model.requirement = pyo.Constraint(model.J, rule=requirement_rule)

    def objective_rule(model):
        return sum(assignment_cost[i][j] * model.x[i, j] for i in model.I for j in model.J)
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}