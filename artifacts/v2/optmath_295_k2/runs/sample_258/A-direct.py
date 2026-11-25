import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    persons = list(range(7))
    projects = list(range(6))

    capacity_person = params["capacity_person"]
    demand_project = params["demand_project"]
    cost_assign = params["cost_assign"]
    max_person_project = params["max_person_project"]

    model = pyo.ConcreteModel()
    model.i = pyo.Set(initialize=persons)
    model.j = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.i, model.j, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(cost_assign[i][j] * m.x[i, j] for i in m.i for j in m.j)
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def person_capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.j) <= capacity_person[i]
    model.person_capacity_con = pyo.Constraint(model.i, rule=person_capacity_rule)

    def project_demand_rule(m, j):
        return sum(m.x[i, j] for i in m.i) == demand_project[j]
    model.project_demand_con = pyo.Constraint(model.j, rule=project_demand_rule)

    def pair_limit_rule(m, i, j):
        return m.x[i, j] <= max_person_project[i][j]
    model.pair_limit_con = pyo.Constraint(model.i, model.j, rule=pair_limit_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}