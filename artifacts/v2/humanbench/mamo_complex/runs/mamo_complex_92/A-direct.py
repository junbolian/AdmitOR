import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        ("S", "2", params["edge_S_2"]),
        ("S", "3", params["edge_S_3"]),
        ("2", "4", params["edge_2_4"]),
        ("2", "3", params["edge_2_3"]),
        ("3", "5", params["edge_3_5"]),
        ("3", "6", params["edge_3_6"]),
        ("4", "6", params["edge_4_6"]),
        ("5", "T", params["edge_5_T"]),
        ("6", "7", params["edge_6_7"]),
        ("7", "T", params["edge_7_T"]),
    ]

    nodes = ["S", "2", "3", "4", "5", "6", "7", "T"]

    model = pyo.ConcreteModel()
    model.NODES = pyo.Set(initialize=nodes)
    model.EDGES = pyo.Set(initialize=[(u, v) for (u, v, w) in edges])
    model.edge_w = pyo.Param(model.EDGES, initialize={(u, v): w for (u, v, w) in edges})

    # Build undirected incidence: out-edges minus in-edges.
    # Treat each listed edge as traversable in both directions.
    directed = []
    for (u, v, w) in edges:
        directed.append((u, v, w))
        directed.append((v, u, w))

    model.model_x = pyo.Var(model.EDGES, domain=pyo.NonNegativeReals)
    model.x_undirected = pyo.Var(
        [(u, v) for (u, v, w) in directed], domain=pyo.NonNegativeReals
    )

    # Link undirected flows to the base edge variables using a symmetric relation.
    # Simpler approach: use separate directed variables directly.
    model.x = pyo.Var(
        [(u, v) for (u, v, w) in directed], domain=pyo.NonNegativeReals
    )

    def flow_balance_rule(m, n):
        outflow = sum(m.x[(u, v)] for (u, v, w) in directed if u == n)
        inflow = sum(m.x[(u, v)] for (u, v, w) in directed if v == n)
        if n == "S":
            return outflow - inflow == 1
        if n == "T":
            return outflow - inflow == -1
        return outflow - inflow == 0

    model.flow_con = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    # Optional: prevent immediate cancellation on paired arcs (keep nonnegative).
    # Objective: minimize total weighted flow.
    model.obj = pyo.Objective(
        expr=sum(w * model.x[(u, v)] for (u, v, w) in directed),
        sense=pyo.minimize,
    )

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}