import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_costs"]
    caps = params["pair_capacities"]

    n_emp = len(availability)
    n_proj = len(requirements)
    employees = list(range(n_emp))
    projects = list(range(n_proj))
    pairs = [(i, j) for i in employees for j in projects]

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(costs[i][j] * mdl.assign[i, j] for (i, j) in pairs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def emp_cap_rule(mdl, i):
        return sum(mdl.assign[i, j] for j in projects) <= availability[i]

    model.emp_cap = pyo.Constraint(employees, rule=emp_cap_rule)

    def proj_req_rule(mdl, j):
        return sum(mdl.assign[i, j] for i in employees) == requirements[j]

    model.proj_req = pyo.Constraint(projects, rule=proj_req_rule)

    def pair_cap_rule(mdl, i, j):
        return mdl.assign[i, j] <= caps[i][j]

    model.pair_cap = pyo.Constraint(pairs, rule=pair_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}