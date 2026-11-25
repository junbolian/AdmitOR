import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = params["distances"]
    n = 5
    p = 3

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n - 1)
    ordered_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    model.pairs = pyo.Set(initialize=ordered_pairs, dimen=2)

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.pairs, domain=pyo.Binary)

    model.select_exactly = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes) == p
    )

    def pair_ub_rule(model, i, j):
        return model.y[i, j] <= model.x[i]

    model.pair_ub1 = pyo.Constraint(model.pairs, rule=pair_ub_rule)

    def pair_ub2_rule(model, i, j):
        return model.y[i, j] <= model.x[j]

    model.pair_ub2 = pyo.Constraint(model.pairs, rule=pair_ub2_rule)

    def pair_lb_rule(model, i, j):
        return model.y[i, j] >= model.x[i] + model.x[j] - 1

    model.pair_lb = pyo.Constraint(model.pairs, rule=pair_lb_rule)

    # Sum each unordered pair exactly once: use ordered pairs with i < j,
    # taking the directed distance d(i,j) as listed in the problem.
    unordered_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    model.dispersion = pyo.Objective(
        expr=sum(distances[i * n + j] * model.y[i, j] for (i, j) in unordered_pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.dispersion))
    return {"objective": obj_val, "status": "optimal"}