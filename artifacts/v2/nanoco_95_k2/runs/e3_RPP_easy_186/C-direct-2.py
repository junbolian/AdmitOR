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
                dist[i, j] = 0.0
            elif i < j:
                if i == 2 and j == 4:
                    dist[i, j] = params["dist_2_4_asym"]
                elif i == 2 and j == 4:
                    dist[i, j] = params["dist_2_4_asym"]
                else:
                    key = f"dist_{i}_{j}"
                    dist[i, j] = params[key]
                    dist[j, i] = params[key]
            # i > j handled by symmetric case above, except asym pairs

    # Handle asymmetric pairs explicitly
    dist[2, 4] = params["dist_2_4_asym"]
    dist[4, 2] = params["dist_4_2_asym"]

    # Re-fill symmetric pairs correctly (overwrite what loop may have set wrong)
    symmetric_pairs = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),
        (1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),
        (2,3),(2,5),(2,6),(2,7),(2,8),
        (3,4),(3,5),(3,6),(3,7),(3,8),
        (4,5),(4,6),(4,7),(4,8),
        (5,6),(5,7),(5,8),
        (6,7),(6,8),
        (7,8)
    ]
    for (i, j) in symmetric_pairs:
        key = f"dist_{i}_{j}"
        v = params[key]
        dist[i, j] = v
        dist[j, i] = v

    # Graph edges (undirected service network)
    graph_edges = [(0,3),(1,7),(2,3),(2,8),(3,5),(3,7),(4,5),(4,6),(5,7),(5,8)]
    # Required edges (must be traversed at least once)
    required_edges = {(0,3),(1,7),(2,8),(3,7),(4,5),(4,6),(5,7),(5,8)}

    # This is a Route Inspection / Chinese Postman variant on a directed multigraph.
    # We model it as a min-cost flow / arc-routing problem.
    # 
    # Approach: 
    # - Each required edge (u,v) can be traversed in either direction (or both).
    # - We introduce integer variables for how many times each directed arc is used.
    # - Flow conservation at every node.
    # - Subtour elimination via connectivity constraints.
    #
    # Decision variables: x[i,j] = number of times directed arc (i->j) is used
    # For required edge (u,v): x[u,v] + x[v,u] >= 1
    # For non-required graph edges (u,v): x[u,v] + x[v,u] >= 0 (optional traversal)
    # For transit arcs (any i,j not in graph): x[i,j] >= 0 integer (deadheading allowed)
    #
    # Flow conservation: sum_j x[i,j] = sum_j x[j,i] for all i (Eulerian condition)
    # This ensures the route is a closed walk.
    #
    # Subtour elimination: We need all used arcs to form a single connected tour through depot.
    # We'll use the fact that for an Eulerian graph, connectivity + flow conservation suffices
    # if we add connectivity cuts or use a compact formulation.
    #
    # For subtour elimination in this arc-routing context, we use:
    # For every non-empty subset S of nodes not containing depot (0),
    #   sum_{i in S, j not in S} x[i,j] >= 1 if any arc within S is used.
    # 
    # We implement this via lazy constraints (callback).

    all_arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("LazyConstraints", 1)

    # x[i,j]: number of times arc i->j is traversed
    x = model.addVars(all_arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for (i, j) in all_arcs),
        GRB.MINIMIZE
    )

    # Flow conservation: in-degree = out-degree at every node
    for node in range(n):
        model.addConstr(
            gp.quicksum(x[i, node] for i in range(n) if i != node) ==
            gp.quicksum(x[node, j] for j in range(n) if j != node),
            name=f"flow_{node}"
        )

    # Required edges must be traversed at least once (in either direction)
    for (u, v) in required_edges:
        model.addConstr(x[u, v] + x[v, u] >= 1, name=f"req_{u}_{v}")

    # The depot must be used (route must pass through node 0)
    model.addConstr(
        gp.quicksum(x[0, j] for j in range(1, n)) >= 1,
        name="depot_depart"
    )

    # Subtour elimination via lazy constraints callback
    def subtour_callback(model_cb, where):
        if where != GRB.Callback.MIPSOL:
            return

        x_val = model_cb.cbGetSolution(x)

        # Build adjacency from used arcs
        used_arcs = [(i, j) for (i, j) in all_arcs if x_val[i, j] > 0.5]

        if not used_arcs:
            return

        # Find connected components via BFS on the undirected support graph
        neighbors = {i: set() for i in range(n)}
        for (i, j) in used_arcs:
            neighbors[i].add(j)
            neighbors[j].add(i)

        # BFS from depot
        visited = set()
        queue = [0]
        visited.add(0)
        while queue:
            curr = queue.pop()
            for nb in neighbors[curr]:
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        # Find nodes that are used but not reachable from depot
        used_nodes = set()
        for (i, j) in used_arcs:
            used_nodes.add(i)
            used_nodes.add(j)

        unreachable = used_nodes - visited
        if not unreachable:
            return

        # Find connected components among unreachable nodes
        def get_component(start, nodes_set):
            comp = set()
            q = [start]
            comp.add(start)
            while q:
                cur = q.pop()
                for nb in neighbors[cur]:
                    if nb in nodes_set and nb not in comp:
                        comp.add(nb)
                        q.append(nb)
            return comp

        remaining = set(unreachable)
        while remaining:
            start = next(iter(remaining))
            comp = get_component(start, remaining)
            remaining -= comp

            # Add cut: flow leaving component S must be >= 1
            S = comp
            S_complement = [j for j in range(n) if j not in S]
            cut_arcs_out = [(i, j) for i in S for j in S_complement]
            if cut_arcs_out:
                model_cb.cbLazy(
                    gp.quicksum(x[i, j] for (i, j) in cut_arcs_out) >= 1
                )

    model.optimize(subtour_callback)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}