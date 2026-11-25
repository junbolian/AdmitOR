import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["dispersion_weights"]
    num_selected = params["num_facilities_selected"]

    nodes = [0, 1, 2, 3, 4]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    n = len(nodes)

    def weight_of(i, j):
        # weights may be a dict with tuple keys, dict with string keys, or a flat list
        if isinstance(weights, dict):
            if (i, j) in weights:
                return weights[(i, j)]
            key_str = f"{i},{j}"
            if key_str in weights:
                return weights[key_str]
            key_str2 = f"{i}_{j}"
            if key_str2 in weights:
                return weights[key_str2]
            raise KeyError((i, j))
        # assume flat list ordered by (i, j) with i != j
        idx = i * (n - 1) + (j if j < i else j - 1)
        return weights[idx]

    model = pyo.ConcreteModel()

    model.nodes_index = pyo.Set(initialize=nodes)
    model.pairs_index = pyo.Set(initialize=pairs, dimen=2)

    model.select = pyo.Var(model.nodes_index, domain=pyo.Binary)
    model.pair_var = pyo.Var(model.pairs_index, domain=pyo.Binary)

    model.cardinality = pyo.Constraint(
        expr=sum(model.select[i] for i in model.nodes_index) == num_selected
    )

    def pair_ub_i_rule(mdl, i, j):
        return mdl.pair_var[i, j] <= mdl.select[i]

    def pair_ub_j_rule(mdl, i, j):
        return mdl.pair_var[i, j] <= mdl.select[j]

    def pair_lb_rule(mdl, i, j):
        return mdl.pair_var[i, j] >= mdl.select[i] + mdl.select[j] - 1

    model.pair_ub_i = pyo.Constraint(model.pairs_index, rule=pair_ub_i_rule)
    model.pair_ub_j = pyo.Constraint(model.pairs_index, rule=pair_ub_j_rule)
    model.pair_lb = pyo.Constraint(model.pairs_index, rule=pair_lb_rule)

    def objective_rule(mdl):
        return sum(weight_of(i, j) * mdl.pair_var[i, j] for (i, j) in mdl.pairs_index)

    model.total_dispersion = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}