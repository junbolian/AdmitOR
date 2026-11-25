import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
import random


def solve(params):
    total_capacity = params["total_capacity"]
    project_demand = params["project_demand"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    assignment_limit_min = params["assignment_limit_min"]
    assignment_limit_max = params["assignment_limit_max"]

    n_persons = len(total_capacity)
    n_projects = len(project_demand)

    # Deterministic cost and limit parameters derived from ranges.
    rng = random.Random(12345)
    cost = {}
    limit = {}
    for i in range(n_persons):
        for j in range(n_projects):
            cost[(i, j)] = rng.uniform(cost_min, cost_max)
            limit[(i, j)] = rng.uniform(assignment_limit_min, assignment_limit_max)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_persons - 1)
    model.J = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[i, j] for i in model.P for j in model.J),
        sense=pyo.minimize,
    )

    def person_cap_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == total_capacity[i]

    model.person_cap = pyo.Constraint(model.P, rule=person_cap_rule)

    def proj_demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) == project_demand[j]

    model.proj_demand = pyo.Constraint(model.J, rule=proj_demand_rule)

    def limit_rule(m, i, j):
        return m.x[i, j] <= limit[(i, j)]

    model.limit = pyo.Constraint(model.P, model.J, rule=limit_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}