import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    node_coords = params["node_coords"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    service_costs = params["service_costs"]
    travel_cost_matrix = params["travel_cost_matrix"]

    # Required edges (structural, frozen)
    required_edges = [(0,1),(0,2),(1,3),(2,6),(3,4),(3,5),(3,6),(5,6)]
    assert len(required_edges) == num_required_edges
    assert len(required_edges) == num_graph_edges

    num_nodes = len(node_coords)
    nodes = list(range(num_nodes))

    # Service cost per required edge
    edge_service_cost = {required_edges[i]: service_costs[i] for i in range(num_required_edges)}

    # Deadhead cost between any pair of nodes (directed)
    def deadhead(i, j):
        return travel_cost_matrix[i][j]

    # This is the Route Inspection / Chinese Postman problem on an undirected graph.
    # For each required edge (u,v), we decide how many times it is traversed in each direction:
    #   x[u,v] = traversals u->v (service or deadhead)
    #   x[v,u] = traversals v->u (service or deadhead)
    # Net flow on the graph edge contributes service cost once per traversal in either direction
    # (since service cost is for the physical road, not direction).
    # Additional deadhead traversals between arbitrary node pairs are also allowed.
    #
    # We model this as a directed multigraph flow problem:
    # Decision variables:
    #   arc_flow[i,j] = number of times vehicle travels arc i->j (integer >= 0)
    #     - For graph edges (u,v): arcs (u,v) and (v,u) carry the edge's service cost
    #       for each traversal (since each traversal services the road).
    #       But we need each required edge serviced at least once total (either direction counts).
    #     - For deadhead arcs (i,j) not in graph edges: cost = deadhead(i,j), no service.
    #
    # Actually, the cleanest formulation:
    # For each required edge e=(u,v):
    #   y_e = 1 if serviced (required, so y_e >= 1, but since all are required, we enforce >= 1)
    #   The vehicle can traverse the edge in either direction; each traversal contributes service cost.
    #   Let f[u,v] = number of traversals of edge e in direction u->v
    #       f[v,u] = number of traversals in direction v->u
    #   At least one traversal total: f[u,v] + f[v,u] >= 1
    #
    # For non-graph-edge arcs (i,j): deadhead variable d[i,j] >= 0 integer,
    #   cost = deadhead(i,j) * d[i,j]
    #
    # Flow conservation at each node (vehicle returns to depot):
    #   sum of outflow arcs = sum of inflow arcs  for all nodes
    #
    # Objective: minimize total cost
    #   sum over required edges e=(u,v): service_cost[e] * (f[u,v] + f[v,u])
    #   + sum over non-graph arcs (i,j): deadhead(i,j) * d[i,j]
    #
    # Note: deadhead arcs along graph edges are already covered by f[u,v]/f[v,u]
    # since their cost equals the service cost (the problem uses service cost for graph edges
    # and travel cost matrix for deadheading -- but re-traversals of graph edges also
    # incur service cost per traversal).
    # 
    # Wait -- re-reading the problem: service cost is swept distance, deadhead is non-productive.
    # Re-traversals of a required edge could be either another service pass or deadhead.
    # The problem says "traversing certain segments multiple times (either as empty travel 
    # or non-productive driving)". The service cost per segment is a fixed distance cost.
    # Total cost = service cost (for each required edge, once) + deadhead cost for extra travel.
    # 
    # Simplest correct model: treat each traversal of a graph edge as costing service_cost[e]
    # (it's the physical distance), and deadhead arcs between non-adjacent nodes cost travel_cost_matrix.
    # Required edges must be traversed at least once total.

    model = gp.Model("route_inspection")
    model.setParam("OutputFlag", 0)

    # Graph edge set as a set for quick lookup
    graph_edge_set = set(required_edges)
    # Also add reverse direction
    graph_edge_undirected = set()
    for u, v in required_edges:
        graph_edge_undirected.add((u, v))
        graph_edge_undirected.add((v, u))

    # Variables for traversals along graph edges (directed)
    f = {}
    for u, v in required_edges:
        f[(u, v)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"f_{u}_{v}")
        f[(v, u)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"f_{v}_{u}")

    # Variables for deadhead arcs between non-adjacent node pairs
    # (i,j) where (i,j) and (j,i) are not graph edges
    d = {}
    for i in nodes:
        for j in nodes:
            if i != j and (i, j) not in graph_edge_undirected:
                d[(i, j)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"d_{i}_{j}")

    # Each required edge must be traversed at least once (in either direction)
    for u, v in required_edges:
        model.addConstr(f[(u, v)] + f[(v, u)] >= 1, name=f"service_{u}_{v}")

    # Flow conservation: for each node, inflow = outflow
    for nd in nodes:
        outflow = gp.LinExpr()
        inflow = gp.LinExpr()
        # Graph edge arcs
        for u, v in required_edges:
            if u == nd:
                outflow += f[(u, v)]
            if v == nd:
                inflow += f[(u, v)]
            if v == nd:
                outflow += f[(v, u)]
            if u == nd:
                inflow += f[(v, u)]
        # Deadhead arcs
        for i in nodes:
            for j in nodes:
                if i != j and (i, j) not in graph_edge_undirected:
                    if i == nd:
                        outflow += d[(i, j)]
                    if j == nd:
                        inflow += d[(i, j)]
        model.addConstr(outflow == inflow, name=f"flow_conservation_{nd}")

    # Objective: minimize total distance
    obj = gp.LinExpr()
    for u, v in required_edges:
        sc = edge_service_cost[(u, v)]
        obj += sc * f[(u, v)]
        obj += sc * f[(v, u)]
    for (i, j), var in d.items():
        obj += deadhead(i, j) * var

    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}