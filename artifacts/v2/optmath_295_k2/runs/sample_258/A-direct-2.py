import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    capacity_person = params["capacity_person"]
    demand_project = params["demand_project"]
    cost_assign = params["cost_assign"]
    max_person_project = params["max_person_project"]

    num_persons = len(capacity_person)
    num_projects = len(demand_project)

    model = pyo.ConcreteModel()
    model.persons = pyo.RangeSet(0, num_persons - 1)
    model.projects = pyo.RangeSet(0, num_projects - 1)

    model.x = pyo.Var(model.persons, model.projects, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(cost_assign[i][j] * m.x[i, j] for i in m.persons for j in m.projects)
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def person_capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.projects) <= capacity_person[i]
    model.person_capacity = pyo.Constraint(model.persons, rule=person_capacity_rule)

    def project_demand_rule(m, j):
        return sum(m.x[i, j] for i in m.persons) >= demand_project[j]
    model.project_demand = pyo.Constraint(model.projects, rule=project_demand_rule)

    def upper_bound_rule(m, i, j):
        return m.x[i, j] <= max_person_project[i][j]
    model.upper_bound = pyo.Constraint(model.persons, model.projects, rule=upper_bound_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}