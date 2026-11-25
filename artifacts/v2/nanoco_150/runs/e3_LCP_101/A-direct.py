import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cells = params["num_cells"]
    num_links = params["num_links"]
    interference_links = params["interference_links"]
    frequency_pools = params["frequency_pools"]
    num_frequency_bands = params["num_frequency_bands"]

    cells = list(range(num_cells))
    bands = list(range(num_frequency_bands))
    links = list(range(num_links))

    def pool_of(c):
        if isinstance(frequency_pools, dict):
            return list(frequency_pools[c])
        return list(frequency_pools[c])

    def link_of(e):
        if isinstance(interference_links, dict):
            return tuple(interference_links[e])
        return tuple(interference_links[e])

    pools = {c: pool_of(c) for c in cells}
    edges = {e: link_of(e) for e in links}

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=cells)
    model.B = pyo.Set(initialize=bands)
    model.E = pyo.Set(initialize=links)

    model.x = pyo.Var(model.C, model.B, within=pyo.Binary)
    model.z = pyo.Var(within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    def assign_rule(m, c):
        return sum(m.x[c, b] for b in bands if b in pools[c]) == 1

    model.assign_rule = pyo.Constraint(model.C, rule=assign_rule)

    def outside_pool_rule(m, c, b):
        if b in pools[c]:
            return pyo.Constraint.Skip
        return m.x[c, b] == 0

    model.outside_pool_rule = pyo.Constraint(model.C, model.B, rule=outside_pool_rule)

    def link_rule(m, e):
        c1, c2 = edges[e]
        return sum(m.x[c1, b] + m.x[c2, b] for b in bands) <= 1

    model.link_rule = pyo.Constraint(model.E, rule=link_rule)

    def z_rule(m, c, b):
        return m.z >= b * m.x[c, b]

    model.z_rule = pyo.Constraint(model.C, model.B, rule=z_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}