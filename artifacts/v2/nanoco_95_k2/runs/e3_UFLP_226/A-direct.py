import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investment_cost = params["investment_cost"]
    distance_matrix = params["distance_matrix"]

    n_points = len(distance_matrix)
    n_sites = len(distance_matrix[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_points - 1)
    model.S = pyo.RangeSet(0, n_sites - 1)

    model.y = pyo.Var(model.S, domain=pyo.Binary)
    model.x = pyo.Var(model.P, model.S, domain=pyo.Binary)

    def objective_rule(m):
        return (
            sum(investment_cost[s] * m.y[s] for s in m.S)
            + sum(distance_matrix[p][s] * m.x[p, s] for p in m.P for s in m.S)
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def assign_rule(m, p):
        return sum(m.x[p, s] for s in m.S) == 1

    model.assign_con = pyo.Constraint(model.P, rule=assign_rule)

    def link_rule(m, p, s):
        return m.x[p, s] <= m.y[s]

    model.link_con = pyo.Constraint(model.P, model.S, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}