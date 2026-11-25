def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    capacities = params["capacities"]
    weights = params["weights"]

    num_items = len(weights)
    num_dims = len(capacities)
    # Structural upper bound on number of bins: one per item
    num_bins = num_items

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.RangeSet(0, num_items - 1)
    model.BINS = pyo.RangeSet(0, num_bins - 1)
    model.DIMS = pyo.RangeSet(0, num_dims - 1)

    model.x = pyo.Var(model.ITEMS, model.BINS, domain=pyo.Binary)
    model.y = pyo.Var(model.BINS, domain=pyo.Binary)

    # Each item assigned to exactly one bin
    model.assign_con = pyo.Constraint(
        model.ITEMS,
        rule=lambda m, i: sum(m.x[i, b] for b in m.BINS) == 1,
    )

    # Capacity constraints per bin and dimension
    model.cap_con = pyo.Constraint(
        model.BINS,
        model.DIMS,
        rule=lambda m, b, d: sum(weights[i][d] * m.x[i, b] for i in m.ITEMS)
        <= capacities[d] * m.y[b],
    )

    # Symmetry breaking: bin b can only be used if bin b-1 is used
    def _sym_rule(m, b):
        if b == m.BINS.first():
            return pyo.Constraint.Skip
        return m.y[b] <= m.y[b - 1]

    model.sym_con = pyo.Constraint(model.BINS, rule=_sym_rule)

    model.obj = pyo.Objective(expr=sum(model.y[b] for b in model.BINS), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}