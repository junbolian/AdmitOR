import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sizes = list(params["item_sizes"])
    capacity = params["block_capacity"]
    n = len(sizes)

    model = pyo.ConcreteModel()
    item_set = pyo.RangeSet(0, n - 1)
    block_set = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(item_set, block_set, domain=pyo.Binary)
    model.y = pyo.Var(block_set, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.y[b] for b in block_set), sense=pyo.minimize
    )

    model.assign_con = pyo.Constraint(
        item_set,
        rule=lambda m, i: sum(m.x[i, b] for b in block_set) == 1,
    )

    model.capacity_con = pyo.Constraint(
        block_set,
        rule=lambda m, b: sum(sizes[i] * m.x[i, b] for i in item_set)
        <= capacity * m.y[b],
    )

    def _sym_rule(m, b):
        if b == 0:
            return pyo.Constraint.Skip
        return m.y[b] <= m.y[b - 1]

    model.symmetry_con = pyo.Constraint(block_set, rule=_sym_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}