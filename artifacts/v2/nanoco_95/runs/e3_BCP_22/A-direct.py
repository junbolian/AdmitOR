import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = 8
    buffers = {
        (0, 1): params["safety_buffer_0_1"],
        (0, 7): params["safety_buffer_0_7"],
        (1, 4): params["safety_buffer_1_4"],
        (1, 7): params["safety_buffer_1_7"],
        (4, 5): params["safety_buffer_4_5"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.edges = pyo.Set(initialize=list(buffers.keys()), dimen=2)

    # Big-M bound: worst-case span of the chain of constraints
    max_buffer = max(buffers.values())
    span = max_buffer * num_nodes + 1

    model.x = pyo.Var(model.nodes, domain=pyo.NonNegativeIntegers, bounds=(0, span))
    model.z = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, span))

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    model.span_con = pyo.ConstraintList()
    for i in model.nodes:
        model.span_con.add(model.z >= model.x[i])

    def abs_rule(model, u, v):
        d = buffers[(u, v)]
        return model.x[u] - model.x[v] >= d

    def abs_rule_rev(model, u, v):
        d = buffers[(u, v)]
        return model.x[v] - model.x[u] >= d

    model.abs_con = pyo.Constraint(model.edges, rule=pyo.Disjunction_rule if False else None) if False else None
    # Build disjunctive constraints explicitly using binary selectors
    model.sel = pyo.Var(model.edges, within=pyo.Binary)
    M = span

    model.diff_pos = pyo.Constraint(
        model.edges,
        rule=lambda m, u, v: m.x[u] - m.x[v] >= buffers[(u, v)] - M * (1 - m.sel[u, v]),
    )
    model.diff_neg = pyo.Constraint(
        model.edges,
        rule=lambda m, u, v: m.x[v] - m.x[u] >= buffers[(u, v)] - M * m.sel[u, v],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}