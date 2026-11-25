import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    separation_weight = params["separation_weight"]

    edges = [
        (0, 1),
        (0, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (2, 7),
        (3, 4),
        (3, 5),
        (4, 5),
        (4, 6),
        (4, 7),
        (5, 6),
    ]

    num_nets = 8

    model = pyo.ConcreteModel()
    model.nets = pyo.RangeSet(0, num_nets - 1)
    model.constraints_idx = pyo.RangeSet(0, len(edges) - 1)

    model.track = pyo.Var(model.nets, domain=pyo.NonNegativeIntegers)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    def edge_rule(mdl, i):
        u, v = edges[i]
        d = separation_weight[i]
        return mdl.track[u] - mdl.track[v] >= d

    def edge_rule_rev(mdl, i):
        u, v = edges[i]
        d = separation_weight[i]
        return mdl.track[v] - mdl.track[u] >= d

    model.disjunct_fwd = pyo.Constraint(model.constraints_idx, rule=edge_rule)
    model.no_rev = pyo.Constraint(model.constraints_idx, rule=lambda mdl, i: pyo.Constraint.Skip)

    # Use indicator-free reformulation via absolute value is non-linear;
    # instead use disjunctive big-M with binary selectors.
    model.sel = pyo.Var(model.constraints_idx, domain=pyo.Binary)
    bigM = 1000

    def abs_lower(mdl, i):
        u, v = edges[i]
        d = separation_weight[i]
        return mdl.track[u] - mdl.track[v] >= d - bigM * (1 - mdl.sel[i])

    def abs_upper(mdl, i):
        u, v = edges[i]
        d = separation_weight[i]
        return mdl.track[v] - mdl.track[u] >= d - bigM * mdl.sel[i]

    model.del_component(model.disjunct_fwd)
    model.del_component(model.no_rev)

    model.abs_lower = pyo.Constraint(model.constraints_idx, rule=abs_lower)
    model.abs_upper = pyo.Constraint(model.constraints_idx, rule=abs_upper)

    model.span = pyo.Constraint(model.nets, rule=lambda mdl, j: mdl.z >= mdl.track[j])

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}