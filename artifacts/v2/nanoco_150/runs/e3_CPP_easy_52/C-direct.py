import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    num_nodes = params["num_nodes"]
    depot = params["depot"]
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]
    num_graph_edges = params["num_graph_edges"]
    graph_edges = params["graph_edges"]
    num_required_edges = params["num_required_edges"]
    required_edges = params["required_edges"]
    edge_costs = params["edge_costs"]

    nodes = list(range(num_nodes))

    # Build service cost lookup for required edges
    service_cost = {}
    for entry in edge_costs:
        u, v, c = entry[0], entry[1], entry[2]
        service_cost[(u, v)] = c
        service_cost[(v, u)] = c

    # Required edges set (undirected)
    req_set = set()
    for e in required_edges:
        u, v = e[0], e[1]
        req_set.add((min(u, v), max(u, v)))

    # This is a Route Inspection / Chinese Postman problem on an undirected graph.
    # The carrier must traverse all required edges at least once, and can deadhead
    # between any pair of nodes using distance_matrix costs.
    #
    # Approach: Model as a mixed integer program.
    # For each required edge (u,v), we have integer variable x[u,v] >= 1 (number of traversals).
    # For each ordered pair (i,j), we have integer variable d[i,j] >= 0 (deadhead traversals).
    # Flow conservation at each node must hold (Eulerian condition).
    #
    # The degree of node i from required edges: each traversal of edge (u,v) contributes
    # 1 to degree of u and 1 to degree of v.
    # Deadhead arc d[i,j] contributes 1 to out-degree of i, 1 to in-degree of j.
    #
    # For an Eulerian circuit to exist on the multigraph, each node must have even degree.
    # We model this by tracking the degree parity.
    #
    # Let x[u,v] = number of times required edge (u,v) is traversed (>= 1).
    # Let d[i,j] = number of deadhead traversals from i to j (directed, >= 0).
    #
    # Degree of node i = sum of x[e] for all required edges e incident to i
    #                  + sum of d[i,j] for all j (out deadhead)
    #                  + sum of d[j,i] for all j (in deadhead)
    #
    # For Eulerian circuit: degree of every node must be even.
    # Also, the graph must be connected (guaranteed if we allow deadheading).
    #
    # Since deadhead arcs are undirected in cost but we need to track flow,
    # we use undirected deadhead variables d[i,j] for i < j, each >= 0 integer,
    # contributing to degree of both i and j.
    #
    # Parity constraint: for each node i,
    #   (sum of x[e] for edges e incident to i) + (sum of d[e] for deadhead edges e incident to i) ≡ 0 (mod 2)
    #
    # Since x[e] >= 1 for required edges, parity of required degree is fixed by x[e] mod 2.
    # We want total degree even, so deadhead edges must fix the parity of odd-degree nodes.
    #
    # This is equivalent to the T-join / Chinese Postman formulation.
    # For minimum cost, we only need to add deadhead edges between odd-degree nodes.
    # With x[e]=1 for all required edges, compute odd-degree nodes, then find min cost
    # perfect matching. But since x[e] can be > 1, we allow that too.
    #
    # For a full ILP formulation:

    model = gp.Model("chinese_postman")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # Variables
    # x[u,v] for each required edge, integer >= 1
    x = {}
    req_list = list(req_set)
    for (u, v) in req_list:
        x[(u, v)] = model.addVar(vtype=GRB.INTEGER, lb=1, name=f"x_{u}_{v}")

    # d[i,j] for i < j, all pairs, integer >= 0 (deadhead traversals)
    d = {}
    for i in nodes:
        for j in nodes:
            if i < j:
                d[(i, j)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"d_{i}_{j}")

    model.update()

    # Objective: minimize total cost
    obj = gp.LinExpr()
    for (u, v) in req_list:
        obj += service_cost[(u, v)] * x[(u, v)]
    for (i, j) in d:
        obj += distance_matrix[i][j] * d[(i, j)]
    model.setObjective(obj, GRB.MINIMIZE)

    # Parity (Eulerian) constraints: degree of each node must be even
    # degree of node i = sum_{required edges (u,v) incident to i} x[(u,v)]
    #                  + sum_{deadhead edges (i,j) or (j,i)} d[(min,max)]
    # must be even, i.e., ≡ 0 mod 2
    #
    # We enforce this using binary auxiliary variables b[i] in {0,1}:
    # degree[i] = 2 * b_sum[i]  (i.e., degree is even)
    # This is equivalent to: degree[i] mod 2 == 0
    # We use: degree[i] = 2 * slack[i], slack[i] >= 0 integer

    slack = {}
    for i in nodes:
        slack[i] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"slack_{i}")
    model.update()

    for i in nodes:
        degree_expr = gp.LinExpr()
        # Required edges incident to i
        for (u, v) in req_list:
            if u == i or v == i:
                degree_expr += x[(u, v)]
        # Deadhead edges incident to i
        for (a, b_) in d:
            if a == i or b_ == i:
                degree_expr += d[(a, b_)]
        model.addConstr(degree_expr == 2 * slack[i], name=f"euler_{i}")

    # Connectivity: the traversed edges must form a connected multigraph
    # We enforce this via flow conservation: there must exist a circulation
    # through all required edges starting and ending at depot.
    #
    # Add flow variables f[i,j] for directed flow on each edge traversal.
    # For required edge (u,v) traversed x times: flow can go u->v or v->u each traversal.
    # For deadhead (i,j) traversed d times: similarly directed.
    #
    # Actually, for the Chinese Postman on undirected graphs, the parity constraint
    # (all nodes even degree) is sufficient to guarantee Eulerian circuit existence
    # IF the graph is connected. We need to ensure connectivity.
    #
    # We'll add a connectivity constraint via a flow formulation:
    # Send 1 unit of flow from depot to every other node using the traversed edges.
    # If edge (u,v) is traversed at least once (x or d >= 1), flow can pass through it.

    # Flow for connectivity: f_conn[i,j] >= 0, continuous
    # On required edge (u,v): can send flow in either direction, capacity = x[(u,v)] (at least 1)
    # On deadhead (i,j): can send flow in either direction, capacity = d[(i,j)]
    # But d[(i,j)] might be 0, so we need to be careful.
    #
    # To avoid complexity, use a simpler big-M connectivity via reachability.
    # Actually, for this small problem (8 nodes), let's add subtour elimination via
    # a single-commodity flow for connectivity.

    # Flow variables for connectivity (directed)
    fc = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                fc[(i, j)] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"fc_{i}_{j}")
    model.update()

    # Flow conservation for connectivity:
    # Depot (node 0) is source sending (num_nodes - 1) units total (1 to each other node)
    # Each other node receives exactly 1 unit net
    for i in nodes:
        in_flow = gp.quicksum(fc[(j, i)] for j in nodes if j != i)
        out_flow = gp.quicksum(fc[(i, j)] for j in nodes if j != i)
        if i == depot:
            model.addConstr(out_flow - in_flow == num_nodes - 1, name=f"conn_flow_{i}")
        else:
            model.addConstr(in_flow - out_flow == 1, name=f"conn_flow_{i}")

    # Capacity constraints: flow can only use edges that are traversed
    # For required edge (u,v): fc[u,v] + fc[v,u] <= (num_nodes-1) * x[(u,v)]
    # For deadhead (i,j) i<j: fc[i,j] + fc[j,i] <= (num_nodes-1) * d[(i,j)]
    #   but d could be 0, so we need binary indicator or big-M with d >= flow/(N-1)
    #
    # Use big-M: if x[(u,v)] >= 1, that edge exists. We allow flow up to (N-1) per traversal.
    M_conn = num_nodes - 1

    for (u, v) in req_list:
        model.addConstr(fc[(u, v)] + fc[(v, u)] <= M_conn * x[(u, v)], name=f"cap_req_{u}_{v}")

    for (i, j) in d:
        # Need binary indicator for whether deadhead edge is used
        # Instead: fc[i,j] + fc[j,i] <= M * d[i,j]
        # This works since d[i,j] >= 0 integer; if d=0, no flow allowed
        model.addConstr(fc[(i, j)] + fc[(j, i)] <= M_conn * d[(i, j)], name=f"cap_dead_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj_val = model.ObjVal
        stat_str = "optimal" if status == GRB.OPTIMAL else "time_limit_feasible"
        return {"objective": float(obj_val), "status": "optimal" if status == GRB.OPTIMAL else stat_str}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}