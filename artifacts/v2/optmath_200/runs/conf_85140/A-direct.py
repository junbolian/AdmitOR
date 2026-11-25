import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dispersion_scores = params["dispersion_scores"]
    facilities_to_select = params["facilities_to_select"]
    num_facilities = params["num_facilities"]

    pairs = [(k, l) for k in range(num_facilities) for l in range(num_facilities) if k != l]

    model = pyo.ConcreteModel()

    model.facility_index = pyo.RangeSet(0, num_facilities - 1)
    model.pair_index = pyo.Set(initialize=pairs, dimen=2)

    model.select_facility = pyo.Var(model.facility_index, domain=pyo.Binary)
    model.activate_pair = pyo.Var(model.pair_index, domain=pyo.Binary)

    model.exact_selection = pyo.Constraint(
        expr=sum(model.select_facility[i] for i in model.facility_index) == facilities_to_select
    )

    def pair_link_rule(mdl, k, l):
        return mdl.activate_pair[k, l] <= mdl.select_facility[k]

    def pair_link_rule2(mdl, k, l):
        return mdl.activate_pair[k, l] <= mdl.select_facility[l]

    model.pair_link_first = pyo.Constraint(model.pair_index, rule=pair_link_rule)
    model.pair_link_second = pyo.Constraint(model.pair_index, rule=pair_link_rule2)

    score_map = {}
    for idx, pair in enumerate(pairs):
        score_map[pair] = dispersion_scores[idx]

    model.total_dispersion = pyo.Objective(
        expr=sum(score_map[(k, l)] * model.activate_pair[k, l] for (k, l) in pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}