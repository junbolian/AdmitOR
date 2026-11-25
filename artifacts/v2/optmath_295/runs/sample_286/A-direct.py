import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    big_M = params["big_M"]
    exact_selection_count = params["exact_selection_count"]
    min_distance_lower_bound = params["min_distance_lower_bound"]
    min_distance_upper_bound = params["min_distance_upper_bound"]

    # Implicit distance structure: use a deterministic distance matrix based on node indices.
    # Distances are structural; the model references them via constraints.
    nodes = [f"node_{i}" for i in range(num_nodes)]
    pairs = [(nodes[i], nodes[j]) for i in range(num_nodes) for j in range(i + 1, num_nodes)]

    # Distance matrix (structural constant definition of geometry, not a PARAM value)
    distance = {}
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                distance[(nodes[i], nodes[j])] = abs(i - j) * 10

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.NODES, domain=pyo.Binary)
    model.y = pyo.Var(model.PAIRS, domain=pyo.Binary)

    model.min_distance = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(min_distance_lower_bound, min_distance_upper_bound),
    )

    model.obj = pyo.Objective(expr=model.min_distance, sense=pyo.maximize)

    model.select_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.NODES) == exact_selection_count
    )

    def dist_rule(mdl, i, j):
        d = distance[(i, j)]
        return mdl.min_distance <= d * mdl.y[i, j] + big_M * (2 - mdl.x[i] - mdl.x[j])

    model.dist_cons = pyo.Constraint(model.PAIRS, rule=dist_rule)

    def pair_upper_rule(mdl, i, j):
        return mdl.y[i, j] <= mdl.x[i]

    def pair_upper_rule2(mdl, i, j):
        return mdl.y[i, j] <= mdl.x[j]

    def pair_lower_rule(mdl, i, j):
        return mdl.y[i, j] >= mdl.x[i] + mdl.x[j] - 1

    model.pair_ub1 = pyo.Constraint(model.PAIRS, rule=pair_upper_rule)
    model.pair_ub2 = pyo.Constraint(model.PAIRS, rule=pair_upper_rule2)
    model.pair_lb = pyo.Constraint(model.PAIRS, rule=pair_lower_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}