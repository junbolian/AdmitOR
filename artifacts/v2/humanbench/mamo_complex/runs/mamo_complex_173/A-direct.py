import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(7))
    source = 0
    sink = 6

    cap = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    val = float(params[key]) if params[key] is not None else 0.0
                else:
                    val = 0.0
                if val > 0:
                    cap[(i, j)] = val

    arcs = list(cap.keys())

    model = pyo.ConcreteModel()
    model.flow = pyo.Var(arcs, bounds=lambda m, i, j: (0, cap[(i, j)]))

    def flow_balance_rule(m, k):
        if k == source:
            return sum(m.flow[i, j] for (i, j) in arcs if i == k) - \
                   sum(m.flow[i, j] for (i, j) in arcs if j == k) == \
                   sum(m.flow[i, j] for (i, j) in arcs if i == source) - \
                   sum(m.flow[i, j] for (i, j) in arcs if j == source)
        return sum(m.flow[i, j] for (i, j) in arcs if i == k) == \
               sum(m.flow[i, j] for (i, j) in arcs if j == k)

    # Source balance placeholder to define variable used; replace with proper formulation
    model.del_component('flow_balance_rule') if hasattr(model, 'flow_balance_rule') else None

    # Correct flow balance: conservation at all nodes except source and sink
    def balance_rule(m, k):
        if k == source or k == sink:
            return pyo.Constraint.Skip
        return sum(m.flow[i, j] for (i, j) in arcs if i == k) - \
               sum(m.flow[i, j] for (i, j) in arcs if j == k) == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in arcs if i == source) -
             sum(model.flow[i, j] for (i, j) in arcs if j == source),
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}