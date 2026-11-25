import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage_scores = params["coverage_scores"]
    num_centers = params["num_centers"]

    nodes = list(range(5))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    # Build score lookup from row-major flattened list (excluding diagonal)
    score_map = {}
    idx = 0
    for i in nodes:
        for j in nodes:
            if i != j:
                score_map[(i, j)] = coverage_scores[idx]
                idx += 1

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.z = pyo.Var(pairs, domain=pyo.Binary)

    model.centers_con = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == num_centers
    )

    def z_upper_rule(model, i, j):
        # z_ij <= x_i and z_ij <= x_j  (linearized AND)
        return model.z[i, j] <= model.x[i] + model.x[j] - (model.x[i] + model.x[j])
    
    # z_ij <= x_i
    model.z_le_xi = pyo.Constraint(
        pairs, rule=lambda model, i, j: model.z[i, j] <= model.x[i]
    )
    # z_ij <= x_j
    model.z_le_xj = pyo.Constraint(
        pairs, rule=lambda model, i, j: model.z[i, j] <= model.x[j]
    )
    # z_ij >= x_i + x_j - 1
    model.z_ge = pyo.Constraint(
        pairs, rule=lambda model, i, j: model.z[i, j] >= model.x[i] + model.x[j] - 1
    )

    def obj_rule(model):
        return sum(score_map[(i, j)] * model.z[i, j] for (i, j) in pairs)

    model.total_coverage = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_coverage))
    return {"objective": obj_val, "status": "optimal"}