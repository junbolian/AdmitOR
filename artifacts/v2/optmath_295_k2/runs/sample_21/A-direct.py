import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_distances = params["pairwise_distances"]
    num_open = params["num_facilities_to_open"]

    if isinstance(raw_distances, dict):
        distances = {tuple(int(k) for k in pair): float(val)
                     for pair, val in raw_distances.items()}
    else:
        distances = {}
        for pair, val in raw_distances:
            pair_t = tuple(int(k) for k in pair)
            distances[pair_t] = float(val)

    nodes = sorted({idx for pair in distances for idx in pair})
    pairs = list(distances.keys())

    model = pyo.ConcreteModel()

    model.facility_set = pyo.Set(initialize=nodes, ordered=True)
    model.arc_set = pyo.Set(initialize=pairs, dimen=2)

    model.open_facility = pyo.Var(model.facility_set, domain=pyo.Binary)
    model.pick_pair = pyo.Var(model.arc_set, domain=pyo.Binary)

    def objective_rule(m):
        return sum(distances[p] * m.pick_pair[p] for p in m.arc_set)
    model.total_dispersion = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def exact_open_rule(m):
        return sum(m.open_facility[idx] for idx in m.facility_set) == num_open
    model.exact_open_con = pyo.Constraint(rule=exact_open_rule)

    def pair_upper_i_rule(m, i, j):
        return m.pick_pair[i, j] <= m.open_facility[i]
    model.pair_upper_i_con = pyo.Constraint(model.arc_set, rule=pair_upper_i_rule)

    def pair_upper_j_rule(m, i, j):
        return m.pick_pair[i, j] <= m.open_facility[j]
    model.pair_upper_j_con = pyo.Constraint(model.arc_set, rule=pair_upper_j_rule)

    def pair_lower_rule(m, i, j):
        return m.pick_pair[i, j] >= m.open_facility[i] + m.open_facility[j] - 1
    model.pair_lower_con = pyo.Constraint(model.arc_set, rule=pair_lower_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}