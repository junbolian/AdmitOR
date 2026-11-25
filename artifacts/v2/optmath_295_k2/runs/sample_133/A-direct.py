import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_select = params["num_facilities_to_select"]
    M = params["large_constant_M"]

    dist = {
        (0, 1): params["distance_01"],
        (0, 2): params["distance_02"],
        (0, 3): params["distance_03"],
        (0, 4): params["distance_04"],
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 4): params["distance_34"],
    }

    nodes = list(range(5))
    pairs = list(dist.keys())

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.y = pyo.Var(pairs, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    model.select_exactly = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == num_select
    )

    def pair_lb_rule(m, i, j):
        return m.y[(i, j)] <= m.x[i]

    def pair_lb2_rule(m, i, j):
        return m.y[(i, j)] <= m.x[j]

    def pair_ub_rule(m, i, j):
        return m.y[(i, j)] >= m.x[i] + m.x[j] - 1

    model.pair_lb = pyo.Constraint(pairs, rule=pair_lb_rule)
    model.pair_lb2 = pyo.Constraint(pairs, rule=pair_lb2_rule)
    model.pair_ub = pyo.Constraint(pairs, rule=pair_ub_rule)

    def min_dist_rule(m, i, j):
        return m.z + M * m.y[(i, j)] <= dist[(i, j)] + M

    model.min_dist = pyo.Constraint(pairs, rule=min_dist_rule)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}