import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    # Normalize weights into a dict keyed by (i, j)
    if isinstance(weights, dict):
        weight_map = {(int(i), int(j)): float(v) for (i, j), v in weights.items()}
    else:
        # Assume list of entries: ((i, j), value) or [i, j, value]
        weight_map = {}
        for entry in weights:
            if isinstance(entry, dict):
                weight_map[(int(entry["i"]), int(entry["j"]))] = float(entry["value"])
            elif len(entry) == 2 and isinstance(entry[1], (int, float)):
                (i, j) = entry[0] if isinstance(entry[0], (tuple, list)) else entry
                weight_map[(int(i), int(j))] = float(entry[1])
            else:
                weight_map[(int(entry[0]), int(entry[1]))] = float(entry[2])

    model = pyo.ConcreteModel()

    nodes = sorted({i for (i, j) in weight_map} | {j for (i, j) in weight_map})
    pairs = list(weight_map.keys())

    model.nodes = pyo.Set(initialize=nodes)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.pairs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(weight_map[(i, j)] * m.y[(i, j)] for (i, j) in m.pairs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def facility_count_rule(m):
        return sum(m.x[i] for i in m.nodes) == num_facilities

    model.facility_count = pyo.Constraint(rule=facility_count_rule)

    def activation_i_rule(m, i, j):
        return m.y[(i, j)] <= m.x[i]

    model.activation_i = pyo.Constraint(model.pairs, rule=activation_i_rule)

    def activation_j_rule(m, i, j):
        return m.y[(i, j)] <= m.x[j]

    model.activation_j = pyo.Constraint(model.pairs, rule=activation_j_rule)

    def activation_xy_rule(m, i, j):
        return m.y[(i, j)] >= m.x[i] + m.x[j] - 1

    model.activation_xy = pyo.Constraint(model.pairs, rule=activation_xy_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}