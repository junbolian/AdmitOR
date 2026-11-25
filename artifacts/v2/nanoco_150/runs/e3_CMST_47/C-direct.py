import gurobipy as gp
from gurobipy import GRB

def solve(params):
    node_coordinates = params["node_coordinates"]
    edge_costs = params["edge_costs"]
    max_branch_size = params["max_branch_size"]

    n = 12
    nodes = list(range(n))
    non_root = list(range(1, n))

    # Build full symmetric cost matrix from upper-triangle edge_costs
    cost = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                cost[i][j] = 0
            elif i < j:
                cost[i][j] = edge_costs[i][j]
            else:
                cost[i][j] = edge_costs[j][i]

    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    model = gp.Model("radial_feeder")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if undirected edge (i,j) is in the tree (i < j)
    x = {}
    for (i, j) in edges:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Tree: exactly n-1 edges
    model.addConstr(gp.quicksum(x[i, j] for (i, j) in edges) == n - 1, name="tree_edges")

    # Multi-commodity flow: one unit from root (0) to each non-root node k
    f = {}
    for k in non_root:
        for (i, j) in edges:
            f[k, i, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"f_{k}_{i}_{j}")
            f[k, j, i] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"f_{k}_{j}_{i}")

    # Flow capacity: flow only on active edges
    for (i, j) in edges:
        model.addConstr(
            gp.quicksum(f[k, i, j] for k in non_root) <= (n - 1) * x[i, j],
            name=f"cap_{i}_{j}_fwd"
        )
        model.addConstr(
            gp.quicksum(f[k, j, i] for k in non_root) <= (n - 1) * x[i, j],
            name=f"cap_{i}_{j}_rev"
        )

    # Flow conservation for each commodity k at each node
    for k in non_root:
        for node in nodes:
            in_f = []
            out_f = []
            for (i, j) in edges:
                if j == node:
                    in_f.append(f[k, i, j])
                    out_f.append(f[k, j, i])
                if i == node:
                    in_f.append(f[k, j, i])
                    out_f.append(f[k, i, j])

            net = gp.quicksum(in_f) - gp.quicksum(out_f)
            if node == 0:
                model.addConstr(net == -1, name=f"flow_src_{k}")
            elif node == k:
                model.addConstr(net == 1, name=f"flow_dst_{k}")
            else:
                model.addConstr(net == 0, name=f"flow_transit_{k}_{node}")

    # Branch membership: bm[c, v] = 1 if node v is in the subtree of child c of root
    bm = {}
    for c in non_root:
        for v in non_root:
            bm[c, v] = model.addVar(vtype=GRB.BINARY, name=f"bm_{c}_{v}")

    # Link bm to flow on arc 0 -> c
    for c in non_root:
        for v in non_root:
            model.addConstr(f[v, 0, c] <= bm[c, v], name=f"bm_ub_{c}_{v}")
            model.addConstr(f[v, 0, c] >= bm[c, v], name=f"bm_lb_{c}_{v}")

    # Each non-root node belongs to exactly one branch
    for v in non_root:
        model.addConstr(
            gp.quicksum(bm[c, v] for c in non_root) == 1,
            name=f"one_branch_{v}"
        )

    # Branch size limit: subtree of child c has at most max_branch_size nodes
    for c in non_root:
        model.addConstr(
            gp.quicksum(bm[c, v] for v in non_root) <= max_branch_size * x[0, c],
            name=f"branch_size_{c}"
        )

    # Objective: minimize total cable cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for (i, j) in edges),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}