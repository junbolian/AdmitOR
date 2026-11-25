import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    distance_cost = params["distance_cost"]
    n_neigh = params["num_neighborhoods"]
    n_cand = params["num_candidates"]

    neighborhoods = list(range(n_neigh))
    candidates = list(range(n_cand))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=neighborhoods, ordered=True)
    model.J = pyo.Set(initialize=candidates, ordered=True)

    model.x = pyo.Var(model.J, domain=pyo.Binary)
    model.y = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_cost[j] * m.x[j] for j in m.J) + \
               sum(distance_cost[i][j] * m.y[i, j] for i in m.I for j in m.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.y[i, j] for j in m.J) == 1

    model.assign_con = pyo.Constraint(model.I, rule=assign_rule)

    def link_rule(m, i, j):
        return m.y[i, j] <= m.x[j]

    model.link_con = pyo.Constraint(model.I, model.J, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}