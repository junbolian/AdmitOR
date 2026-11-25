import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance = params["distance"]
    num_open = params["num_facilities_open"]

    def get_dist(i, j):
        return distance[i][j]

    n = len(distance)
    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n - 1)
    model.pairs = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j]
    )

    model.select = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_active = pyo.Var(model.pairs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(get_dist(i, j) * m.pair_active[i, j] for (i, j) in m.pairs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.facility_limit = pyo.Constraint(
        expr=sum(model.select[k] for k in model.nodes) == num_open
    )

    def pair_link_rule(m, i, j):
        return m.pair_active[i, j] <= m.select[i]

    def pair_link_rule2(m, i, j):
        return m.pair_active[i, j] <= m.select[j]

    def pair_link_rule3(m, i, j):
        return m.pair_active[i, j] >= m.select[i] + m.select[j] - 1

    model.pair_link = pyo.Constraint(model.pairs, rule=pair_link_rule)
    model.pair_link2 = pyo.Constraint(model.pairs, rule=pair_link_rule2)
    model.pair_link3 = pyo.Constraint(model.pairs, rule=pair_link_rule3)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}