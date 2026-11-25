import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dispersion_weights = params["dispersion_weights"]
    total_facilities = params["total_facilities"]

    n = 5
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    weights = {pair: dispersion_weights[k] for k, pair in enumerate(pairs)}

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=list(range(n)))
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.select = pyo.Var(model.nodes, domain=pyo.Binary)
    model.act = pyo.Var(model.pairs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(weights[(i, j)] * model.act[i, j] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    model.total_facilities_con = pyo.Constraint(
        expr=sum(model.select[i] for i in model.nodes) == total_facilities
    )

    def pair_logic_rule(m, i, j):
        return m.act[i, j] <= m.select[i]
    model.pair_logic_a = pyo.Constraint(model.pairs, rule=pair_logic_rule)

    def pair_logic_rule_b(m, i, j):
        return m.act[i, j] <= m.select[j]
    model.pair_logic_b = pyo.Constraint(model.pairs, rule=pair_logic_rule_b)

    def pair_logic_rule_c(m, i, j):
        return m.act[i, j] >= m.select[i] + m.select[j] - 1
    model.pair_logic_c = pyo.Constraint(model.pairs, rule=pair_logic_rule_c)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}