import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    member_time = params["member_time"]
    project_effort = params["project_effort"]
    assignment_cost = params["assignment_cost"]
    per_pair_capacity = params["per_pair_capacity"]

    n_person = len(member_time)
    n_project = len(project_effort)

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, n_person - 1)
    model.J = pyo.RangeSet(0, n_project - 1)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(assignment_cost[p][j] * m.x[p, j]
                   for p in m.P for j in m.J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.member_balance = pyo.Constraint(
        model.P,
        rule=lambda m, p: sum(m.x[p, j] for j in m.J) == member_time[p]
    )

    model.project_balance = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.x[p, j] for p in m.P) == project_effort[j]
    )

    model.pair_capacity = pyo.Constraint(
        model.P, model.J,
        rule=lambda m, p, j: m.x[p, j] <= per_pair_capacity[p][j]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}