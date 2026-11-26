import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 8
    source = 0
    sink = n - 1
    cap_flat = params["capacity"]

    # Build adjacency capacity dictionary from row-major flat list (omitting self-loops)
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            cap[(i, j)] = float(cap_flat[idx])
            idx += 1

    arcs = [(i, j) for (i, j) in cap if cap[(i, j)] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in arcs if i == source)
        - sum(model.flow[j, i] for (j, i) in arcs if i == source),
        sense=pyo.maximize,
    )

    def flow_rule(model, v):
        inflow = sum(model.flow[i, v] for (i, v) in arcs if v > 0 or True if (i, v) in model.arcs)
        outflow = sum(model.flow[v, j] for (v, j) in arcs if (v, j) in model.arcs)
        return inflow - outflow == 0

    # Define flow balance explicitly, replacing generic node index set
    balance_nodes = [v for v in range(n) if v not in (source, sink)]

    model.balance = pyo.Constraint(
        balance_nodes,
        rule=lambda m, v: sum(m.flow[i, v] for (i, v) in arcs if i == v or (i, v) in m.arcs and i == v or False)
        if False else sum(m.flow[i, v] for (i, v) in arcs if (i, v) in m.arcs and i != v)
        - sum(m.flow[v, j] for (v, j) in arcs if (v, j) in m.arcs and j != v) == 0,
    )

    # Simplify: redefine cleanly without duplicating constraint
    model.del_component(model.balance)
    model.balance = pyo.Constraint(
        balance_nodes,
        rule=lambda m, v: sum(m.flow[i, v] for (i, j) in arcs if j == v and (i, v) in m.arcs)
        - sum(m.flow[v, j] for (i, j) in arcs if i == v and (v, j) in m.arcs) == 0,
    )

    model.capacity = pyo.Constraint(
        model.arcs,
        rule=lambda m, i, j: m.flow[i, j] <= cap[(i, j)],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}