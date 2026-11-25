import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    node_coords = params["node_coords"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    service_costs = params["service_costs"]
    travel_cost_matrix = params["travel_cost_matrix"]

    # Required edges (structural, fixed by problem statement)
    required_edges = [(0,1),(0,2),(1,3),(2,6),(3,4),(3,5),(3,6),(5,6)]
    assert len(required_edges) == num_required_edges
    assert len(required_edges) == num_graph_edges

    num_nodes = 7
    nodes = list(range(num_nodes))

    # Service cost dict
    service_cost = {required_edges[i]: service_costs[i] for i in range(num_required_edges)}

    # Travel cost helper
    def tcost(i, j):
        return travel_cost_matrix[i][j]

    # This is the Route Inspection / Chinese Postman problem on an undirected graph.
    # We need every required edge traversed at least once, flow conservation at every node,
    # and the tour is closed (starts and ends at node 0).
    #
    # Formulation:
    # For each required (undirected) edge (i,j), introduce directed variables:
    #   x[i,j] >= 1 if traversed i->j direction (service counts)
    #   x[j,i] >= 1 if traversed j->i direction (service counts)
    # At least one direction must be used at least once.
    # For deadhead travel between any pair of nodes (i,j), introduce:
    #   d[i,j] >= 0 integer (non-negative directed deadhead traversals)
    #
    # Flow conservation at every node:
    #   sum of outflow = sum of inflow
    #
    # Constraint: for each required edge (i,j):
    #   x[i,j] + x[j,i] >= 1  (must be serviced at least once in some direction)
    #
    # Objective: minimize sum of service costs * x + sum of travel costs * d

    model = gp.Model("cpp")
    model.setParam("OutputFlag", 0)

    # Directed service traversal variables for required edges
    # x[(i,j)] = number of times edge (i,j) is traversed in direction i->j (as service)
    x = {}
    for (i, j) in required_edges:
        x[(i, j)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
        x[(j, i)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{j}_{i}")

    # Directed deadhead variables for all ordered pairs
    d = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                d[(i, j)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"d_{i}_{j}")

    model.update()

    # Each required edge must be serviced at least once (in either direction)
    for (i, j) in required_edges:
        model.addConstr(x[(i, j)] + x[(j, i)] >= 1, name=f"service_{i}_{j}")

    # Flow conservation at every node
    # Total flow out of node v = total flow into node v
    service_edge_set = set()
    for (i, j) in required_edges:
        service_edge_set.add((i, j))
        service_edge_set.add((j, i))

    for v in nodes:
        # Outflow: service traversals leaving v + deadhead leaving v
        outflow = []
        for (i, j) in service_edge_set:
            if i == v:
                outflow.append(x[(i, j)])
        for j in nodes:
            if j != v:
                outflow.append(d[(v, j)])

        # Inflow: service traversals entering v + deadhead entering v
        inflow = []
        for (i, j) in service_edge_set:
            if j == v:
                inflow.append(x[(i, j)])
        for i in nodes:
            if i != v:
                inflow.append(d[(i, v)])

        model.addConstr(gp.quicksum(outflow) == gp.quicksum(inflow), name=f"flow_{v}")

    # The tour must actually depart node 0 (non-trivial tour)
    # This is implied by needing to service edges incident to node 0,
    # but we add a minimum departure constraint to avoid zero solution
    model.addConstr(
        gp.quicksum(x[(0, j)] for j in nodes if (0, j) in x) +
        gp.quicksum(x[(j, 0)] for j in nodes if (j, 0) in x) +
        gp.quicksum(d[(0, j)] for j in nodes if j != 0) >= 1,
        name="depart_depot"
    )

    # Objective: total cost = service traversals * service cost + deadhead * travel cost
    obj_terms = []
    for (i, j) in required_edges:
        sc = service_cost[(i, j)]
        obj_terms.append(sc * x[(i, j)])
        obj_terms.append(sc * x[(j, i)])
    for i in nodes:
        for j in nodes:
            if i != j:
                obj_terms.append(tcost(i, j) * d[(i, j)])

    model.setObjective(gp.quicksum(obj_terms), GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}