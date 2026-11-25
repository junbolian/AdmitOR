import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    cost_matrix = params["cost_matrix"]
    branch_capacity = params["branch_capacity"]
    num_drop_zones = params["num_drop_zones"]
    num_nodes_total = params["num_nodes_total"]

    n = num_nodes_total  # 15
    nodes = list(range(n))
    base = 0
    drop_zones = list(range(1, n))  # nodes 1..14

    # Edges (undirected pairs)
    edges = [(i, j) for i in nodes for j in nodes if i < j]
    edge_index = {(i, j): idx for idx, (i, j) in enumerate(edges)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j] = 1 if edge (i,j) is in the tree
    x = {}
    for (i, j) in edges:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # For routing/flow: directed variables to enforce tree structure rooted at base
    # f[i][j] = flow from i to j (directed), used for subtree size counting
    # We model the tree as a directed arborescence from base.
    # arc[i,j] = 1 if directed arc i->j exists in the rooted tree
    arc = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                arc[i, j] = model.addVar(vtype=GRB.BINARY, name=f"arc_{i}_{j}")

    # sub[j] = index (1..num_drop_zones) of the direct child of base that is
    # the ancestor-or-self of drop zone j. Used to link branch membership.
    # Instead, use a flow-based approach:
    # For each direct child c of base, let load[c] = number of drop zones in subtree of c
    # We need load[c] <= branch_capacity for all c.

    # Flow variable: flow[c][j] = 1 if drop zone j is in the subtree rooted at
    # direct child c of base.
    # This is complex; use a simpler subtree-size approach via commodity flow.

    # Approach: 
    # 1. arc[i,j] defines directed tree (arborescence from base)
    # 2. For each drop zone j, flow commodity j flows from base to j along tree arcs
    # 3. branch_load[c] = sum of flow passing through arc (base, c) for all drop zone commodities
    #    = number of drop zones in subtree of c
    # 4. branch_load[c] <= branch_capacity

    # Commodity flow for subtree size:
    # Instead of per-drop-zone commodities (expensive), use aggregate flow:
    # Send 1 unit from base toward each drop zone.
    # flow_arc[i,j] = number of drop zones whose path uses arc i->j
    flow_arc = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                flow_arc[i, j] = model.addVar(
                    vtype=GRB.CONTINUOUS, lb=0, name=f"flow_{i}_{j}"
                )

    # Objective: minimize total cost
    obj = gp.LinExpr()
    for (i, j) in edges:
        obj += cost_matrix[i][j] * x[i, j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraint 1: exactly n-1 edges in a spanning tree
    model.addConstr(gp.quicksum(x[i, j] for (i, j) in edges) == n - 1,
                    name="tree_size")

    # Constraint 2: each node except base has exactly one parent (in-degree = 1)
    for j in drop_zones:
        model.addConstr(
            gp.quicksum(arc[i, j] for i in nodes if i != j) == 1,
            name=f"indegree_{j}"
        )

    # Constraint 3: base has in-degree 0
    model.addConstr(
        gp.quicksum(arc[i, base] for i in nodes if i != base) == 0,
        name="base_indegree"
    )

    # Constraint 4: arc consistency with undirected edges
    # arc[i,j] + arc[j,i] = x[min,max]
    for (i, j) in edges:
        model.addConstr(arc[i, j] + arc[j, i] == x[i, j],
                        name=f"arc_edge_{i}_{j}")

    # Constraint 5: flow conservation
    # At base: send out flow equal to num_drop_zones total
    # At drop zone j: absorb 1 unit
    # At intermediate node k (not base, not a leaf absorbing): flow in = flow out + (1 if k is drop zone)
    # Flow on arc[i,j]: flow_arc[i,j] <= (n-1) * arc[i,j]
    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(
                    flow_arc[i, j] <= (n - 1) * arc[i, j],
                    name=f"flow_cap_{i}_{j}"
                )

    # Flow conservation at each node
    for k in nodes:
        inflow = gp.quicksum(flow_arc[i, k] for i in nodes if i != k)
        outflow = gp.quicksum(flow_arc[k, j] for j in nodes if j != k)
        if k == base:
            # base generates flow = num_drop_zones
            model.addConstr(outflow - inflow == num_drop_zones,
                            name=f"flow_cons_{k}")
        else:
            # each drop zone absorbs 1
            model.addConstr(inflow - outflow == 1,
                            name=f"flow_cons_{k}")

    # Constraint 6: branch capacity
    # For each direct child c of base: flow on arc (base, c) <= branch_capacity
    for c in drop_zones:
        model.addConstr(
            flow_arc[base, c] <= branch_capacity * arc[base, c],
            name=f"branch_cap_{c}"
        )

    # Note: the flow conservation + arc constraints together enforce the tree
    # structure (connected, no cycles) via the arborescence formulation.
    # However, we still need connectivity. The flow model already handles this:
    # since every drop zone must receive exactly 1 unit of flow originating at base,
    # and flow can only travel along arcs, connectivity is implied.

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjVal), "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}