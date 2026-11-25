import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    dist_flat = params["distance_matrix"]
    
    # Reconstruct 7x7 distance matrix
    n = 7
    dist = [[dist_flat[i * n + j] for j in range(n)] for i in range(n)]
    
    # Required edges (undirected)
    required_edges = [(0, 1), (1, 3), (2, 6), (3, 4), (3, 5), (3, 6), (5, 6)]
    
    # This is the Route Inspection / Chinese Postman problem on a subset of edges.
    # We need a closed walk starting/ending at node 0 that covers all required edges
    # at least once, minimizing total distance (including deadhead traversals).
    #
    # Approach: Model as a min-cost flow / integer program.
    # Variables: x[i][j] = number of times arc (i->j) is traversed (directed)
    # For each required undirected edge (u,v), x[u][v] + x[v][u] >= 1
    # Flow balance: for each node, in-flow == out-flow
    # Objective: minimize sum of dist[i][j] * x[i][j]
    #
    # To handle connectivity (the walk must be connected), we add subtour elimination.
    # Since this is on directed arcs and we need an Eulerian circuit on the traversed
    # subgraph, connectivity is enforced via subtour elimination on nodes that are
    # actually visited.

    # Build directed arc set (all pairs i != j)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # x[i,j] = number of times arc i->j is traversed
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")
    
    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )
    
    # Flow balance: for each node, sum of outflow == sum of inflow
    for k in range(n):
        model.addConstr(
            gp.quicksum(x[k, j] for j in range(n) if j != k) ==
            gp.quicksum(x[i, k] for i in range(n) if i != k),
            name=f"balance_{k}"
        )
    
    # Required edges must be covered at least once (in either direction)
    for (u, v) in required_edges:
        model.addConstr(x[u, v] + x[v, u] >= 1, name=f"req_{u}_{v}")
    
    # Depot must be used (tour starts and ends at 0)
    model.addConstr(
        gp.quicksum(x[0, j] for j in range(1, n)) >= 1,
        name="depot_depart"
    )
    
    # Subtour elimination via connectivity constraints.
    # For every proper non-empty subset S of nodes that contains node 0,
    # the flow leaving S must be >= 1 if any required edge has both endpoints in S
    # but the tour must leave S.
    # 
    # More precisely: enforce that the solution is a single connected tour.
    # We use the standard subtour elimination for TSP-like problems:
    # For every subset S not containing all nodes and not empty,
    # if S contains node 0, then there must be at least one arc leaving S.
    #
    # Since n=7, we can enumerate all subsets.
    
    # Add subtour elimination: for each subset S containing node 0 (1 <= |S| < n),
    # sum of x[i,j] for i in S, j not in S >= 1
    # (This ensures the tour cannot be confined to S alone.)
    
    nodes = list(range(n))
    for size in range(1, n):
        for subset in itertools.combinations(nodes, size):
            subset_set = set(subset)
            if 0 not in subset_set:
                continue
            complement = [v for v in nodes if v not in subset_set]
            if not complement:
                continue
            # At least one arc must leave subset
            model.addConstr(
                gp.quicksum(x[i, j] for i in subset_set for j in complement) >= 1,
                name=f"subtour_{'_'.join(map(str, subset))}"
            )
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}