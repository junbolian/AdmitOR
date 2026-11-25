import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    member_time = params["member_time"]
    project_effort = params["project_effort"]
    assignment_cost = params["assignment_cost"]
    per_pair_capacity = params["per_pair_capacity"]

    persons = list(range(6))
    projects = list(range(8))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=persons)
    model.J = pyo.Set(initialize=projects)
    model.PJ = pyo.Set(initialize=[(p, j) for p in persons for j in projects])

    model.x = pyo.Var(model.PJ, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(assignment_cost[p][j] * m.x[p, j] for p in persons for j in projects)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    model.member_limit = pyo.Constraint(
        model.P,
        rule=lambda m, p: sum(m.x[p, j] for j in projects) == member_time[p],
    )

    model.project_req = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.x[p, j] for p in persons) == project_effort[j],
    )

    model.pair_cap = pyo.Constraint(
        model.PJ,
        rule=lambda m, p, j: m.x[p, j] <= per_pair_capacity[p][j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}