import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    cost = params["cost"]
    pair_capacity = params["pair_capacity"]

    n_persons = len(capacity)
    n_projects = len(demand)

    model = pyo.ConcreteModel()

    model.persons = pyo.RangeSet(0, n_persons - 1)
    model.projects = pyo.RangeSet(0, n_projects - 1)

    def x_bounds(m, i, j):
        return (0, pair_capacity[i][j])

    model.x = pyo.Var(model.persons, model.projects, bounds=x_bounds)

    def objective_rule(m):
        return sum(cost[i][j] * m.x[i, j]
                   for i in m.persons for j in m.projects)

    model.objective_expr = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def person_capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.projects) <= capacity[i]

    model.person_capacity_con = pyo.Constraint(model.persons,
                                               rule=person_capacity_rule)

    def project_demand_rule(m, j):
        return sum(m.x[i, j] for i in m.persons) == demand[j]

    model.project_demand_con = pyo.Constraint(model.projects,
                                              rule=project_demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective_expr))
    return {"objective": obj_val, "status": "optimal"}