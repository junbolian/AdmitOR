import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 8
    edge_costs = params["edge_costs"]
    src_excess = params["node0_outflow_inflow_excess"]
    snk_excess = params["node7_inflow_outflow_excess"]

    # Build ordered edge list per the documented ordering
    edges = [(i, j) for i in range(n) for j in range(n) if i != j]
    cost_map = {e: edge_costs[k] for k, e in enumerate(edges)}

    model = pyo.ConcreteModel()
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.x = pyo.Var(model.edges, within=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(cost_map[e] * model.x[e] for e in model.edges),
        sense=pyo.minimize,
    )

    # Flow balance
    model.balance = pyo.ConstraintList()
    for v in range(n):
        out_expr = sum(model.x[(v, j)] for j in range(n) if j != v)
        in_expr = sum(model.x[(i, v)] for i in range(n) if i != v)
        net = out_expr - in_expr
        if v == 0:
            model.balance.add(net == src_excess)
        elif v == n - 1:
            model.balance.add(net == -snk_excess)
        else:
            model.balance.add(net == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}