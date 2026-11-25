import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pairwise_distances = params["pairwise_distances"]
    n_open = params["num_facilities_to_open"]

    # pairwise_distances is a list of ((i, j), value) or (i, j, value)?
    # Handle it as a list of entries; build a dict keyed by (i, j).
    if isinstance(pairwise_distances, dict):
        dist_map = dict(pairwise_distances)
    else:
        dist_map = {}
        for entry in pairwise_distances:
            if isinstance(entry, (list, tuple)) and len(entry) == 3:
                i, j, val = entry
                dist_map[(i, j)] = val
            else:
                key, val = entry
                dist_map[tuple(key)] = val

    facilities = sorted({i for (i, j) in dist_map.keys()} | {j for (i, j) in dist_map.keys()})
    arcs = [(i, j) for (i, j) in dist_map.keys() if i < j]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facilities, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.open_facility = pyo.Var(model.F, domain=pyo.Binary)
    model.use_pair = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(dist_map[(i, j)] * m.use_pair[i, j] for (i, j) in m.A)

    model.total_dispersion = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.exact_open = pyo.Constraint(
        expr=sum(model.open_facility[i] for i in model.F) == n_open
    )

    def pair_rule_i(m, i, j):
        return m.use_pair[i, j] <= m.open_facility[i]

    def pair_rule_j(m, i, j):
        return m.use_pair[i, j] <= m.open_facility[j]

    model.link_i = pyo.Constraint(model.A, rule=pair_rule_i)
    model.link_j = pyo.Constraint(model.A, rule=pair_rule_j)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}