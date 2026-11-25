import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    n = params["num_nodes"]  # 12
    num_edges = params["num_candidate_edges"]  # 23

    # Build coordinate list from params
    coords = []
    for i in range(n):
        x = params[f"node_{i}_x"]
        y = params[f"node_{i}_y"]
        coords.append((x, y))

    candidate_edges = list(params["candidate_edges"])
    leaf_reward = params["leaf_reward"]
    leaf_degree_target = params["leaf_degree_target"]

    # Build edge index list (ensure consistent ordering)
    edges = [(int(u), int(v)) for u, v in candidate_edges]
    E = range(len(edges))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: x[e] = 1 if edge e is selected
    x = model.addVars(E, vtype=GRB.BINARY, name="x")

    # degree[i] = sum of x[e] for edges incident to node i
    degree = {}
    for i in range(n):
        incident = [e for e in E if edges[e][0] == i or edges[e][1] == i]
        degree[i] = gp.quicksum(x[e] for e in incident)

    # Spanning tree requires exactly n-1 edges
    model.addConstr(gp.quicksum(x[e] for e in E) == n - 1, name="num_edges")

    # Each node must have degree >= 1 (connected)
    for i in range(n):
        model.addConstr(degree[i] >= 1, name=f"deg_lb_{i}")

    # Subtour elimination via Miller-Tucker-Zemlin (MTZ) formulation
    # We root the tree at node 0
    # For each directed version of the selected edges, enforce order variables
    # We use a flow-based connectivity formulation instead (more natural for trees)
    # Flow: send 1 unit from node 0 to every other node
    # For each edge (u,v), flow can go either direction if edge is selected

    # Directed flow variables: f[e, 0] = flow from u->v, f[e, 1] = flow from v->u
    f = model.addVars(E, 2, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="f")

    # Flow conservation at each non-root node: net inflow = 1
    for i in range(1, n):
        inflow = []
        outflow = []
        for e in E:
            u, v = edges[e]
            if v == i:
                inflow.append(f[e, 0])   # u->v arrives at i
                outflow.append(f[e, 1])  # v->u leaves i
            elif u == i:
                inflow.append(f[e, 1])   # v->u arrives at i
                outflow.append(f[e, 0])  # u->v leaves i
        model.addConstr(
            gp.quicksum(inflow) - gp.quicksum(outflow) == 1,
            name=f"flow_cons_{i}"
        )

    # Flow only allowed on selected edges; capacity = (n-1)*x[e]
    for e in E:
        model.addConstr(f[e, 0] + f[e, 1] <= (n - 1) * x[e], name=f"flow_cap_{e}")

    # Leaf indicator: is_leaf[i] = 1 if degree[i] == leaf_degree_target
    # We linearize: is_leaf[i] = 1 iff degree[i] == leaf_degree_target
    # Since degree is integer and leaf_degree_target is typically 1,
    # use: is_leaf[i] <= 1 - (degree[i] - t)/M  and  is_leaf[i] >= ...
    # Easier: introduce binary is_leaf[i], constrain degree[i] == leaf_degree_target * is_leaf[i] + (something)*( 1 - is_leaf[i])
    # 
    # Better approach: is_leaf[i] = 1 iff degree[i] == t
    # degree[i] in [1, n-1], t = leaf_degree_target
    # is_leaf[i] <= 1 means degree[i] could be t or not
    # Use big-M:
    #   degree[i] >= t - M*(1 - is_leaf[i])   =>  if is_leaf=1, degree >= t
    #   degree[i] <= t + M*(1 - is_leaf[i])   =>  if is_leaf=1, degree <= t
    #   degree[i] - t >= 1 - M*is_leaf[i] - (n-1)*(...)  -- if is_leaf=0, degree != t
    # This is tricky. Use two auxiliary binaries instead.
    # 
    # Simpler for maximization: relax to is_leaf[i] <= indicator
    # Since we maximize leaves, the solver won't set is_leaf=1 spuriously if
    # we only add the "if is_leaf=1 then degree=t" direction.
    # But we also need "if degree=t then is_leaf can be 1".
    # 
    # Use: degree[i] >= t*is_leaf[i]  (if leaf, degree >= t)
    #      degree[i] <= t + (n-1)*(1 - is_leaf[i])  (if leaf, degree <= t)
    # Together these force: is_leaf[i]=1 => degree[i]=t
    # For maximization, solver will set is_leaf[i]=1 whenever possible (degree=t).

    t = leaf_degree_target
    M_deg = n - 1  # max possible degree

    is_leaf = model.addVars(n, vtype=GRB.BINARY, name="is_leaf")

    for i in range(n):
        # is_leaf[i] = 1 => degree[i] == t
        model.addConstr(degree[i] >= t * is_leaf[i], name=f"leaf_lb_{i}")
        model.addConstr(degree[i] <= t + M_deg * (1 - is_leaf[i]), name=f"leaf_ub_{i}")
        # is_leaf[i] = 0 when degree[i] != t (forced by objective maximization + above)
        # Also add: if degree[i] == t, is_leaf[i] can be 1 (not forced to 0)
        # This is already ensured since objective maximizes is_leaf sum.

    # Objective: maximize leaf_reward * number of leaf nodes
    model.setObjective(leaf_reward * gp.quicksum(is_leaf[i] for i in range(n)), GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}