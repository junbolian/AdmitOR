import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = params["distances"]

    n = 5
    nodes = list(range(n))
    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    # Use the given directed distance for the ordered (i,j) with i<j
    def pair_dist(i, j):
        if isinstance(distances, dict):
            try:
                return distances[(i, j)]
            except (KeyError, TypeError):
                pass
        # Fallback: assume flat list of directed values in row-major order
        return distances[i * n + j]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.pairs, domain=pyo.Binary)

    model.select_exactly_3 = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes) == 3
    )

    def pair_link_rule(m, i, j):
        return m.y[(i, j)] <= m.x[i]

    def pair_link_rule2(m, i, j):
        return m.y[(i, j)] <= m.x[j]

    def pair_link_rule3(m, i, j):
        return m.y[(i, j)] >= m.x[i] + m.x[j] - 1

    model.pair_link_a = pyo.Constraint(model.pairs, rule=pair_link_rule)
    model.pair_link_b = pyo.Constraint(model.pairs, rule=pair_link_rule2)
    model.pair_link_c = pyo.Constraint(model.pairs, rule=pair_link_rule3)

    def dispersion_obj(m):
        return sum(pair_dist(i, j) * m.y[(i, j)] for (i, j) in m.pairs)

    model.total_dispersion = pyo.Objective(rule=dispersion_obj, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}