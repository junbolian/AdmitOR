import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_nodes = 12
    nodes = list(range(n_nodes))
    non_root = list(range(1, n_nodes))

    # Build distance matrix from params
    dist = [[0] * n_nodes for _ in range(n_nodes)]
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            key = f"distance_{i}_{j}"
            d = params[key]
            dist[i][j] = d
            dist[j][i] = d

    max_route_nodes = params["max_route_nodes"]

    model = gp.Model("school_bus_tree")
    model.Params.OutputFlag = 0

    # x[i,j] = 1 if edge from i to j is in the tree (i is parent of j)
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # f[i,j,k] = flow of commodity k on edge from i to j
    f = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                for k in non_root:
                    f[i, j, k] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f"f_{i}_{j}_{k}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each non-root node has exactly one parent
    for j in non_root:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"parent_{j}"
        )

    # No edges into the root
    for i in nodes:
        if i != 0:
            model.addConstr(x[i, 0] == 0, name=f"no_edge_to_root_{i}")

    # Multi-commodity flow: 1 unit from depot to each non-root node
    for k in non_root:
        # Source: node 0 sends 1 unit (outflow - inflow = 1)
        model.addConstr(
            gp.quicksum(f[0, j, k] for j in nodes if j != 0)
            - gp.quicksum(f[j, 0, k] for j in nodes if j != 0) == 1,
            name=f"source_{k}"
        )
        # Sink: node k receives 1 unit (inflow - outflow = 1)
        model.addConstr(
            gp.quicksum(f[j, k, k] for j in nodes if j != k)
            - gp.quicksum(f[k, j, k] for j in nodes if j != k) == 1,
            name=f"sink_{k}"
        )
        # Intermediate nodes: flow conservation (inflow = outflow)
        for nd in nodes:
            if nd != 0 and nd != k:
                model.addConstr(
                    gp.quicksum(f[j, nd, k] for j in nodes if j != nd)
                    - gp.quicksum(f[nd, j, k] for j in nodes if j != nd) == 0,
                    name=f"flow_{nd}_{k}"
                )

    # Flow only on tree edges
    for i in nodes:
        for j in nodes:
            if i != j:
                for k in non_root:
                    model.addConstr(
                        f[i, j, k] <= x[i, j],
                        name=f"flow_edge_{i}_{j}_{k}"
                    )

    # Branch capacity: each direct branch from depot has at most max_route_nodes nodes
    for i in non_root:
        model.addConstr(
            gp.quicksum(f[0, i, k] for k in non_root) <= max_route_nodes * x[0, i],
            name=f"branch_cap_{i}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}