import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    N = 5
    nodes = list(range(N))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    def get_weight(i, j):
        return weights[str(i)][str(j)]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.y = pyo.Var(model.nodes, domain=pyo.Binary)
    model.x = pyo.Var(model.pairs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(get_weight(i, j) * model.x[i, j] for (i, j) in model.pairs),
        sense=pyo.maximize,
    )

    model.facility_count = pyo.Constraint(
        expr=sum(model.y[i] for i in model.nodes) == num_facilities
    )

    def link_rule_i(model, i, j):
        return model.x[i, j] <= model.y[i]

    def link_rule_j(model, i, j):
        return model.x[i, j] <= model.y[j]

    def link_rule_both(model, i, j):
        return model.x[i, j] >= model.y[i] + model.y[j] - 1

    model.link_i = pyo.Constraint(model.pairs, rule=link_rule_i)
    model.link_j = pyo.Constraint(model.pairs, rule=link_rule_j)
    model.link_both = pyo.Constraint(model.pairs, rule=link_rule_both)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}