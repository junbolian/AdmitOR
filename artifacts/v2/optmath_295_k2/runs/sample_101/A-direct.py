import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    scores = params["coverage_scores"]
    num_centers = params["num_centers"]
    num_nodes = params["num_nodes"]

    nodes = list(range(num_nodes))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.z = pyo.Var(pairs, domain=pyo.Binary)

    def score(i, j):
        s = scores[i]
        if isinstance(s, dict):
            return s[j]
        return s[j]

    # Objective: maximize total pairwise coverage
    model.total_coverage = pyo.Objective(
        expr=sum(score(i, j) * model.z[i, j] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    # Exact number of centers
    model.center_count = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == num_centers
    )

    def up_i_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[i]

    def up_j_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[j]

    def low_rule(mdl, i, j):
        return mdl.z[i, j] >= mdl.x[i] + mdl.x[j] - 1

    model.z_le_xi = pyo.Constraint(pairs, rule=up_i_rule)
    model.z_le_xj = pyo.Constraint(pairs, rule=up_j_rule)
    model.z_ge_both = pyo.Constraint(pairs, rule=low_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_coverage))
    return {"objective": obj_val, "status": "optimal"}