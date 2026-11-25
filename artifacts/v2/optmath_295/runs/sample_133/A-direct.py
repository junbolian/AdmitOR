import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p = params["p"]
    n_nodes = params["n_nodes"]
    big_M = params["big_M"]

    dist = {}
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            dist[(i, j)] = params[f"dist_{i}_{j}"]
            dist[(j, i)] = dist[(i, j)]

    pairs = [(i, j) for i in range(n_nodes) for j in range(i + 1, n_nodes)]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=list(range(n_nodes)))
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.z = pyo.Var(model.P, domain=pyo.Binary)
    model.d = pyo.Var(domain=pyo.Reals)

    def obj_rule(m):
        return m.d

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Select exactly p facilities
    def cardinality_rule(m):
        return sum(m.x[i] for i in m.N) == p

    model.cardinality = pyo.Constraint(rule=cardinality_rule)

    # Pairwise linking constraints: z_ij <= x_i and z_ij <= x_j
    model.z_le_x = pyo.Constraint(
        model.P, rule=lambda m, i, j: m.z[i, j] <= m.x[i]
    )
    model.z_le_y = pyo.Constraint(
        model.P, rule=lambda m, i, j: m.z[i, j] <= m.x[j]
    )
    # z_ij >= x_i + x_j - 1
    model.z_ge = pyo.Constraint(
        model.P, rule=lambda m, i, j: m.z[i, j] >= m.x[i] + m.x[j] - 1
    )

    # Minimum distance constraints:
    # d + big_M * z_ij <= (big_M + epsilon_scale) * dist_ij
    scale = big_M + 1.0
    model.mindist = pyo.Constraint(
        model.P,
        rule=lambda m, i, j: m.d + big_M * m.z[i, j] <= scale * dist[(i, j)],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}