import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage_scores = params["coverage_scores"]
    num_centers = params["num_centers"]
    num_nodes = params["num_nodes"]

    nodes = list(range(num_nodes))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    # Normalize coverage_scores into a dict keyed by (i, j)
    if isinstance(coverage_scores, dict):
        score_map = {(i, j): float(coverage_scores[(i, j)]) for (i, j) in pairs}
    else:
        score_map = {(i, j): float(coverage_scores[i][j]) for (i, j) in pairs}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.z = pyo.Var(pairs, domain=pyo.Binary)

    def z_upper_rule(model, i, j):
        return model.z[i, j] <= model.x[i]

    def z_upper2_rule(model, i, j):
        return model.z[i, j] <= model.x[j]

    def z_lower_rule(model, i, j):
        return model.z[i, j] >= model.x[i] + model.x[j] - 1

    model.z_upper_con = pyo.Constraint(pairs, rule=z_upper_rule)
    model.z_upper2_con = pyo.Constraint(pairs, rule=z_upper2_rule)
    model.z_lower_con = pyo.Constraint(pairs, rule=z_lower_rule)

    def centers_rule(model):
        return sum(model.x[i] for i in nodes) == num_centers

    model.centers_con = pyo.Constraint(rule=centers_rule)

    def obj_rule(model):
        return sum(score_map[(i, j)] * model.z[i, j] for (i, j) in pairs)

    model.total_coverage = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_coverage))
    return {"objective": obj_val, "status": "optimal"}