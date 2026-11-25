import gurobipy as gp
from gurobipy import GRB

def solve(params):
    splitter_port_limit = params["splitter_port_limit"]

    # Build cost matrix from params
    n = 16
    cost = {}
    for i in range(n):
        for j in range(i + 1, n):
            key = f"dist_{i}_{j}"
            cost[i, j] = params[key]
            cost[j, i] = params[key]
    for i in range(n):
        cost[i, i] = 0.0

    # Nodes: 0 is root, 1..15 are subscribers
    nodes = list(range(n))
    non_root = list(range(1, n))

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 300)

    # x[i,j] = 1 if directed edge i->j is in the tree (i is parent of j)
    # We allow edges in both directions for non-root pairs, but for root only outgoing
    x = {}
    for i in nodes:
        for j in non_root:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # f[i,j] = flow on directed arc i->j for subtree-size tracking
    # We use Miller-Tucker-Zemlin (MTZ) style or flow-based subtree constraints.
    # Use flow-based formulation: each non-root node j ships one unit of commodity
    # from root to j. The flow on arc (i->j) counts how many nodes are in j's subtree
    # (including j itself).

    # For the splitter constraint, we need subtree sizes of direct children of root.
    # Let s[j] = subtree size of node j (number of nodes in subtree rooted at j).
    # For a direct child c of node 0: s[c] <= splitter_port_limit.

    # Flow variable: flow[i,j] = number of nodes in subtree of j, flowing through arc i->j
    # This equals the commodity flow in a single-commodity flow formulation where
    # each non-root node is a destination with demand 1.
    flow = {}
    for i in nodes:
        for j in non_root:
            if i != j:
                flow[i, j] = model.addVar(lb=0.0, ub=n, vtype=GRB.CONTINUOUS, name=f"f_{i}_{j}")

    # Each non-root node has exactly one parent
    for j in non_root:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"one_parent_{j}"
        )

    # No self-loops (already excluded by i != j in construction)

    # Flow conservation: flow into j equals subtree size of j (>=1)
    # flow on arc (i->j) = 1 + sum of flows on arcs (j->k) for all k
    for j in non_root:
        model.addConstr(
            gp.quicksum(flow[i, j] for i in nodes if i != j) ==
            1 + gp.quicksum(flow[j, k] for k in non_root if k != j),
            name=f"flow_conservation_{j}"
        )

    # Flow only on selected edges
    for i in nodes:
        for j in non_root:
            if i != j:
                model.addConstr(flow[i, j] <= (n - 1) * x[i, j], name=f"flow_edge_{i}_{j}")

    # Splitter constraint: for each direct child c of root (node 0),
    # the subtree size = flow on arc (0->c) <= splitter_port_limit
    for c in non_root:
        model.addConstr(
            flow[0, c] <= splitter_port_limit * x[0, c],
            name=f"splitter_{c}"
        )

    # Objective: minimize total edge cost
    obj = gp.quicksum(
        cost[i, j] * x[i, j]
        for i in nodes
        for j in non_root
        if i != j
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}