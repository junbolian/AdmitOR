import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dispersion_weights = params["dispersion_weights"]
    num_facilities_to_select = params["num_facilities_to_select"]
    num_locations = params["num_locations"]

    model = pyo.ConcreteModel()
    model.locations = pyo.RangeSet(0, num_locations - 1)

    model.selected = pyo.Var(model.locations, domain=pyo.Binary)

    pair_index = []
    pair_weight = {}
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                pair_index.append((i, j))
                pair_weight[(i, j)] = dispersion_weights[i * num_locations + j]

    model.pairs = pyo.Set(initialize=pair_index, dimen=2)
    model.pair_active = pyo.Var(model.pairs, domain=pyo.Binary)

    def objective_rule(m):
        return sum(pair_weight[(i, j)] * m.pair_active[(i, j)] for (i, j) in m.pairs)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    model.select_constraint = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.locations) == num_facilities_to_select
    )

    def pair_lower_rule(m, i, j):
        return m.pair_active[(i, j)] >= m.selected[i] + m.selected[j] - 1

    def pair_upper_i_rule(m, i, j):
        return m.pair_active[(i, j)] <= m.selected[i]

    def pair_upper_j_rule(m, i, j):
        return m.pair_active[(i, j)] <= m.selected[j]

    model.pair_lower = pyo.Constraint(model.pairs, rule=pair_lower_rule)
    model.pair_upper_i = pyo.Constraint(model.pairs, rule=pair_upper_i_rule)
    model.pair_upper_j = pyo.Constraint(model.pairs, rule=pair_upper_j_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}