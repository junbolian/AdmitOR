import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pairwise_benefits = params["pairwise_benefits"]
    num_selected = params["num_selected"]

    nodes = list(range(5))
    ordered_pairs = [(i, j) for i in nodes for j in nodes if i != j]

    # Map ordered pair -> benefit
    benefit_map = {}
    for idx, (i, j) in enumerate(ordered_pairs):
        benefit_map[(i, j)] = pairwise_benefits[idx]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.y = pyo.Var(ordered_pairs, domain=pyo.Binary)

    # Cardinality constraint: exactly num_selected nodes
    model.card = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == num_selected
    )

    # Pairwise activation: y[i,j] == 1 only if both x[i] and x[j] are selected
    # y[i,j] <= x[i], y[i,j] <= x[j], y[i,j] >= x[i] + x[j] - 1
    def pair_ub_first(m, i, j):
        return m.y[(i, j)] <= m.x[i]

    def pair_ub_second(m, i, j):
        return m.y[(i, j)] <= m.x[j]

    def pair_lb(m, i, j):
        return m.y[(i, j)] >= m.x[i] + m.x[j] - 1

    model.pair_ub1 = pyo.Constraint(ordered_pairs, rule=pair_ub_first)
    model.pair_ub2 = pyo.Constraint(ordered_pairs, rule=pair_ub_second)
    model.pair_lb = pyo.Constraint(ordered_pairs, rule=pair_lb)

    def obj_rule(m):
        return sum(benefit_map[(i, j)] * m.y[(i, j)] for (i, j) in ordered_pairs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}