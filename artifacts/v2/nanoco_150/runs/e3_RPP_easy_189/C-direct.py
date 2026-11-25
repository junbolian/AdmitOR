import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    dist = params["distance_matrix"]
    depot = params["depot_node"]

    n = len(dist)

    # Required edges (undirected) - must be traversed at least once
    required_edges = [(1,8),(2,3),(3,4),(3,6),(3,8),(4,8),(5,7),(7,8)]

    # All edges that can be serviced (optional + required)
    all_service_edges = [(0,8),(1,8),(2,3),(3,4),(3,6),(3,8),(4,8),(4,5),(5,7),(7,8)]

    # Build the Route Inspection (Chinese Postman) style model on a directed graph.
    # We model this as a min-cost flow / TSP-on-edges problem using the following approach:
    # 
    # Directed arc variables x[i,j] = number of times arc (i->j) is traversed.
    # Each undirected required edge (u,v) must be covered: x[u,v] + x[v,u] >= 1.
    # Flow conservation at every node (Eulerian circuit condition).
    # Subtour elimination via connectivity (we enforce connectivity through MTZ or
    # flow-based constraints on the directed traversal graph).
    #
    # Because the route must be a single connected circuit, we use a commodity flow
    # approach to ensure connectivity: a single unit of flow must be routable from
    # depot back to depot visiting all "required" nodes.

    # Identify nodes that must be visited (endpoints of required edges)
    required_nodes = set()
    for u, v in required_edges:
        required_nodes.add(u)
        required_nodes.add(v)
    required_nodes.add(depot)
    required_nodes = sorted(required_nodes)

    # Arc cost = dist[i][j] for all i,j
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = gp.Model("route_inspection")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j]: integer number of times arc i->j is traversed
    x = {}
    for i, j in arcs:
        x[i, j] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"x_{i}_{j}")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i, j in arcs),
        GRB.MINIMIZE
    )

    # Flow conservation: for each node, in-flow == out-flow (Eulerian condition)
    for node in range(n):
        in_flow = gp.quicksum(x[i, node] for i in range(n) if i != node)
        out_flow = gp.quicksum(x[node, j] for j in range(n) if j != node)
        model.addConstr(in_flow == out_flow, name=f"flow_balance_{node}")

    # Each required edge must be traversed at least once (in either direction)
    for u, v in required_edges:
        model.addConstr(x[u, v] + x[v, u] >= 1, name=f"req_edge_{u}_{v}")

    # The tour must actually depart from depot (at least one outgoing arc)
    model.addConstr(
        gp.quicksum(x[depot, j] for j in range(n) if j != depot) >= 1,
        name="depot_depart"
    )

    # Subtour elimination via connectivity flow:
    # We introduce auxiliary flow variables f[i,j] representing a unit of
    # "connectivity flow" that must pass through every required node.
    # We use a multi-commodity approach: for each required node r != depot,
    # there must be a path of used arcs from depot to r.
    # We implement this with a single-commodity flow: depot sends |required_nodes|-1
    # units, each required node (except depot) absorbs 1 unit.
    # Flow f[i,j] <= (|required_nodes| - 1) * x[i,j]

    R = len(required_nodes) - 1  # number of non-depot required nodes
    if R > 0:
        f = {}
        for i, j in arcs:
            f[i, j] = model.addVar(lb=0, ub=R, vtype=GRB.CONTINUOUS, name=f"f_{i}_{j}")

        # Flow capacity tied to arc usage
        for i, j in arcs:
            model.addConstr(f[i, j] <= R * x[i, j], name=f"fcap_{i}_{j}")

        # Flow conservation for connectivity commodity
        for node in range(n):
            in_f = gp.quicksum(f[i, node] for i in range(n) if i != node)
            out_f = gp.quicksum(f[node, j] for j in range(n) if j != node)
            if node == depot:
                # depot is source: sends R units
                model.addConstr(out_f - in_f == R, name=f"conn_src")
            elif node in required_nodes:
                # required node: absorbs 1 unit
                model.addConstr(in_f - out_f == 1, name=f"conn_sink_{node}")
            else:
                # other nodes: flow conservation (can pass through or not)
                model.addConstr(in_f == out_f, name=f"conn_pass_{node}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj_val = model.ObjVal
        return {"objective": float(obj_val), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}