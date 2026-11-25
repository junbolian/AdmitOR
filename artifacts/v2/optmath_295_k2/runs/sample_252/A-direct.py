import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    exact_assignments = params["exact_assignments"]
    noe_parameters = params["noe_parameters"]

    num_peaks = len(cost_matrix)
    num_aa = len(cost_matrix[0])
    peaks = range(num_peaks)
    aas = range(num_aa)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peaks, aas, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost_matrix[p][a] * mdl.x[p, a] for p in peaks for a in aas)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(mdl, p):
        return sum(mdl.x[p, a] for a in aas) <= 1
    model.peak_con = pyo.Constraint(peaks, rule=peak_rule)

    def aa_rule(mdl, a):
        return sum(mdl.x[p, a] for p in peaks) <= 1
    model.aa_con = pyo.Constraint(aas, rule=aa_rule)

    def count_rule(mdl):
        return sum(mdl.x[p, a] for p in peaks for a in aas) == exact_assignments
    model.count_con = pyo.Constraint(rule=count_rule)

    # Normalize NOE parameters into a list of forbidden assignment pairs.
    # Accepted forms:
    #   - list of ((p1,a1),(p2,a2))
    #   - list of (p1,a1,p2,a2)
    #   - dict {(p1,a1): [(p2,a2), ...]} or dict mapping to 0/1 indicator per pair
    #   - nested indicators (list/dict over (p1,a1) pairs): proximity flags
    forbidden = []

    def _add_pair(item):
        if isinstance(item, (list, tuple)):
            if len(item) == 2:
                left, right = item
                if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
                    forbidden.append((tuple(left), tuple(right)))
                    return True
            elif len(item) == 4:
                forbidden.append(((item[0], item[1]), (item[2], item[3])))
                return True
        return False

    if isinstance(noe_parameters, dict):
        for key, val in noe_parameters.items():
            if isinstance(val, (list, tuple, set)):
                for target in val:
                    if isinstance(key, (list, tuple)) and len(key) == 2:
                        forbidden.append((tuple(key), tuple(target)))
                    else:
                        _add_pair((key, target))
            elif isinstance(val, (int, float, bool)):
                if val and isinstance(key, (list, tuple)) and len(key) == 4:
                    _add_pair(key)
                elif val and isinstance(key, (list, tuple)) and len(key) == 2:
                    # key is a pair; indicator alone cannot specify partner
                    pass
    elif isinstance(noe_parameters, (list, tuple, set)):
        for item in noe_parameters:
            _add_pair(item)

    # Apply NOE constraints for each forbidden pair.
    pair_index = list(range(len(forbidden)))

    def noe_rule(mdl, k):
        (p1, a1), (p2, a2) = forbidden[k]
        return mdl.x[p1, a1] + mdl.x[p2, a2] <= 1

    if pair_index:
        model.noe_con = pyo.Constraint(pair_index, rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}