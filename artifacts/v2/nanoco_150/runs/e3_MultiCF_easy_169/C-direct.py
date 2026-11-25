import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # Structural constants: undirected edges in problem order
    edges = [(0, 1), (0, 4), (1, 2), (1, 3), (1, 5), (1, 6),
             (2, 3), (3, 4), (4, 5), (5, 6), (5, 9), (6, 7),
             (7, 8), (7, 9), (8, 9)]

    # Directed arcs in the order given by the problem (both directions per edge)
    arcs = []
    for (i, j) in edges:
        arcs.append((i, j))
        arcs.append((j, i))

    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    d1 = params["commodity1_demand"]
    d2 = params["commodity2_demand"]

    # Commodities: (source, sink, demand)
    commodities = [(1, 4, d1), (7, 9, d2)]
    K = len(commodities)
    A = len(arcs)
    N = 10

    # Precompute outgoing/incoming arc index lists per node
    out_arcs = {n: [] for n in range(N)}
    in_arcs = {n: [] for n in range(N)}
    for a in range(A):
        i, j = arcs[a]
        out_arcs[i].append(a)
        in_arcs[j].append(a)

    model = gp.Model("relief_multicommodity")
    model.Params.OutputFlag = 0

    x = {}
    for k in range(K):
        for a in range(A):
            x[k, a] = model.addVar(vtype=GRB.CONTINUOUS, lb=0.0,
                                   name=f"x_{k}_{a}")

    # Objective: minimize total logistics cost across all commodities and arcs
    model.setObjective(
        gp.quicksum(arc_cost[a] * x[k, a] for k in range(K) for a in range(A)),
        GRB.MINIMIZE,
    )

    # Flow conservation per commodity
    for k in range(K):
        s, t, d = commodities[k]
        for n in range(N):
            outflow = gp.quicksum(x[k, a] for a in out_arcs[n])
            inflow = gp.quicksum(x[k, a] for a in in_arcs[n])
            if n == s:
                model.addConstr(outflow - inflow == d, name=f"flow_{k}_src_{n}")
            elif n == t:
                model.addConstr(outflow - inflow == -d, name=f"flow_{k}_sink_{n}")
            else:
                model.addConstr(outflow - inflow == 0, name=f"flow_{k}_{n}")

    # Shared capacity: sum of all commodity flows on an arc <= arc capacity
    for a in range(A):
        model.addConstr(
            gp.quicksum(x[k, a] for k in range(K)) <= arc_capacity[a],
            name=f"cap_{a}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}