import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    # Build distance matrix from params
    n = 9
    dist = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                dist[i, j] = 0
            elif i < j:
                if i == 2 and j == 4:
                    dist[i, j] = params["dist_2_4_asym"]
                elif i == 4 and j == 2:
                    dist[i, j] = params["dist_4_2_asym"]
                else:
                    dist[i, j] = params[f"dist_{i}_{j}"]
                    dist[j, i] = params[f"dist_{i}_{j}"]
            # j < i handled by symmetry above, except asymmetric pairs
    # Fix asymmetric pairs explicitly
    dist[2, 4] = params["dist_2_4_asym"]
    dist[4, 2] = params["dist_4_2_asym"]
    # Re-do symmetric pairs properly
    sym_pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if not (i == 2 and j == 4):
                sym_pairs.append((i, j))
    for (i, j) in sym_pairs:
        dist[i, j] = params[f"dist_{i}_{j}"]
        dist[j, i] = params[f"dist_{i}_{j}"]

    # Graph edges (service infrastructure)
    graph_edges = [(0,3),(1,7),(2,3),(2,8),(3,5),(3,7),(4,5),(4,6),(5,7),(5,8)]
    # Mandatory edges
    mandatory_edges = [(0,3),(1,7),(2,8),(3,7),(4,5),(4,6),(5,7),(5,8)]
    mandatory_set = set(mandatory_edges)

    # This is a Route Inspection / Chinese Postman variant (directed arc routing)
    # on an undirected required edge set, with deadheading allowed on any arc.
    #
    # Formulation: directed arc-flow model.
    # For each undirected required edge {u,v}, we must traverse it at least once
    # in at least one direction. We allow multiple traversals.
    #
    # Decision variables:
    #   x[i,j] = number of times arc (i->j) is traversed, integer >= 0
    #   For required undirected edges {u,v}: x[u,v] + x[v,u] >= 1
    #
    # Flow conservation at each node (directed):
    #   sum_j x[i,j] - sum_j x[j,i] = 0  for all i  (closed tour)
    #
    # Connectivity: all traversed arcs form a single connected tour from depot.
    # We use subtour elimination via connectivity cuts (lazy constraints).

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("LazyConstraints", 1)

    # x[i,j]: number of traversals of arc i->j
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow conservation: closed tour
    for nd in nodes:
        model.addConstr(
            gp.quicksum(x[nd, j] for j in nodes if j != nd) ==
            gp.quicksum(x[j, nd] for j in nodes if j != nd),
            name=f"flow_{nd}"
        )

    # Each required edge traversed at least once (in either direction)
    for (u, v) in mandatory_edges:
        model.addConstr(x[u, v] + x[v, u] >= 1, name=f"req_{u}_{v}")

    # Depot must be used (tour starts/ends at depot)
    model.addConstr(
        gp.quicksum(x[0, j] for j in nodes if j != 0) >= 1,
        name="depot_depart"
    )

    # Subtour elimination via lazy constraints callback
    def subtour_callback(cb_model, where):
        if where == GRB.Callback.MIPSOL:
            x_val = cb_model.cbGetSolution(x)
            # Build adjacency from solution
            # Find connected components of nodes actually visited
            # A node is "active" if it has nonzero flow
            active_nodes = set()
            edges_used = []
            for (i, j) in arcs:
                if x_val[i, j] > 0.5:
                    active_nodes.add(i)
                    active_nodes.add(j)
                    edges_used.append((i, j))

            if not active_nodes:
                return

            # BFS/DFS from depot on undirected version of used arcs
            undirected_neighbors = {nd: set() for nd in active_nodes}
            for (i, j) in edges_used:
                undirected_neighbors[i].add(j)
                undirected_neighbors[j].add(i)

            # BFS from depot
            if 0 not in active_nodes:
                return

            visited = set()
            queue = [0]
            while queue:
                cur = queue.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                for nb in undirected_neighbors.get(cur, []):
                    if nb not in visited:
                        queue.append(nb)

            # Find nodes not reachable from depot
            unreachable = active_nodes - visited
            if not unreachable:
                return

            # Add subtour elimination cut:
            # For any subset S not containing depot, sum of arcs leaving S >= 1
            # We cut by finding a connected component of unreachable nodes
            # and adding a constraint that at least one arc leaves that component.
            comp_visited = set()
            queue2 = [next(iter(unreachable))]
            while queue2:
                cur = queue2.pop()
                if cur in comp_visited:
                    continue
                comp_visited.add(cur)
                for nb in undirected_neighbors.get(cur, []):
                    if nb not in comp_visited and nb in unreachable:
                        queue2.append(nb)

            # S = comp_visited (doesn't contain depot)
            S = comp_visited
            complement = active_nodes - S
            # Arcs from S to complement (including depot side)
            cut_expr = gp.quicksum(
                x[i, j] for i in S for j in nodes if j not in S and i != j
            )
            cb_model.cbLazy(cut_expr >= 1)

    model.optimize(lambda cb_model, where: subtour_callback(cb_model, where))

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}