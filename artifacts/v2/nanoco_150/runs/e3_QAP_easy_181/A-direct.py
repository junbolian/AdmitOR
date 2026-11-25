import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow = params["flow"]
    distance = params["distance"]

    n = 4
    workstations = list(range(n))
    locations = list(range(n))

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(workstations, locations, domain=pyo.Binary)

    def assign_each_ws(m, w):
        return sum(m.assign[w, l] for l in locations) == 1

    def assign_each_loc(m, l):
        return sum(m.assign[w, l] for w in workstations) == 1

    model.ws_constraint = pyo.Constraint(workstations, rule=assign_each_ws)
    model.loc_constraint = pyo.Constraint(locations, rule=assign_each_loc)

    # Introduce a bounded nonnegative variable to linearize bilinear terms.
    pairs = [(w, v, p, q)
             for w in workstations
             for v in workstations
             for p in locations
             for q in locations
             if flow[w][v] != 0 and distance[p][q] != 0]

    model.y = pyo.Var(pairs, domain=pyo.NonNegativeReals, bounds=(0, 1))

    big_m = 1.0

    def link_upper1(m, w, v, p, q):
        return m.y[w, v, p, q] <= m.assign[w, p]

    def link_upper2(m, w, v, p, q):
        return m.y[w, v, p, q] <= m.assign[v, q]

    def link_lower(m, w, v, p, q):
        return m.y[w, v, p, q] >= m.assign[w, p] + m.assign[v, q] - big_m

    model.link1 = pyo.Constraint(pairs, rule=link_upper1)
    model.link2 = pyo.Constraint(pairs, rule=link_upper2)
    model.link3 = pyo.Constraint(pairs, rule=link_lower)

    def cost_expr(m):
        return sum(
            flow[w][v] * distance[p][q] * m.y[w, v, p, q]
            for (w, v, p, q) in pairs
        )

    model.obj = pyo.Objective(rule=cost_expr, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}