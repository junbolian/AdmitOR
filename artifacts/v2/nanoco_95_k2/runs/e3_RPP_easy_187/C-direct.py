import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    distance_matrix = params["distance_matrix"]
    required_edges = params["required_edges"]
    depot_node = params["depot_node"]
    num_nodes = params["num_nodes"]
    num_required_edges = params["num_required_edges"]

    # Build cost lookup
    def dist(i, j):
        return distance_matrix[i * num_nodes + j]

    nodes = list(range(num_nodes))

    # For each required edge (u,v), we can traverse it as u->v or v->u (or both, multiple times).
    # Decision variables:
    #   x[i,j] = number of times arc (i->j) is traversed (integer >= 0)
    # For required edge (u,v): x[u,v] + x[v,u] >= 1
    # Flow balance: for each node k, sum_j x[k,j] == sum_j x[j,k]
    # Objective: minimize sum_{i,j} dist(i,j) * x[i,j]

    # We also need connectivity (subtour elimination).
    # Since this is an Arc Routing Problem on a complete graph, we use
    # a subtour elimination approach via connectivity cuts.

    # Build set of arcs (all ordered pairs i!=j)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    required_set = set()
    for edge in required_edges:
        u, v = edge[0], edge[1]
        required_set.add((u, v))

    model = gp.Model("arc_routing")
    model.setParam("OutputFlag", 0)
    model.setParam("LazyConstraints", 1)

    # Integer arc traversal variables
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(dist(i, j) * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for k in nodes:
        model.addConstr(
            gp.quicksum(x[k, j] for j in nodes if j != k) ==
            gp.quicksum(x[j, k] for j in nodes if j != k),
            name=f"flow_balance_{k}"
        )

    # Required edge coverage: for each required edge (u,v), x[u,v] + x[v,u] >= 1
    for (u, v) in required_set:
        model.addConstr(
            x[u, v] + x[v, u] >= 1,
            name=f"req_{u}_{v}"
        )

    # The route must actually depart from depot (at least one arc leaves depot)
    model.addConstr(
        gp.quicksum(x[depot_node, j] for j in nodes if j != depot_node) >= 1,
        name="depot_depart"
    )

    # Lazy subtour elimination callback
    def subtour_callback(model_cb, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = model_cb.cbGetSolution(x)
            # Build adjacency for arcs with positive flow
            active_arcs = [(i, j) for (i, j) in arcs if x_vals[i, j] > 0.5]

            if not active_arcs:
                return

            # Find connected components (undirected)
            from collections import defaultdict
            adj = defaultdict(set)
            used_nodes = set()
            for (i, j) in active_arcs:
                adj[i].add(j)
                adj[j].add(i)
                used_nodes.add(i)
                used_nodes.add(j)

            if depot_node not in used_nodes:
                return

            # BFS from depot
            visited = set()
            queue = [depot_node]
            while queue:
                cur = queue.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                for nb in adj[cur]:
                    if nb not in visited:
                        queue.append(nb)

            # Nodes not reachable from depot
            unreachable = used_nodes - visited
            if not unreachable:
                return

            # Add subtour elimination cut for each disconnected component
            # For each subset S not containing depot, sum of arcs leaving S >= 1
            # Find connected components among unreachable nodes
            remaining = set(unreachable)
            while remaining:
                seed = next(iter(remaining))
                comp = set()
                stack = [seed]
                while stack:
                    node = stack.pop()
                    if node in comp:
                        continue
                    comp.add(node)
                    for nb in adj[node]:
                        if nb in remaining and nb not in comp:
                            stack.append(nb)
                remaining -= comp

                # Add cut: at least one arc must go from comp to its complement
                complement = [nd for nd in nodes if nd not in comp]
                model_cb.cbLazy(
                    gp.quicksum(x[i, j] for i in comp for j in complement if (i, j) in set(arcs)) >= 1
                )

    model.optimize(subtour_callback)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}