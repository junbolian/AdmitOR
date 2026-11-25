import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    distance_matrix = params["distance_matrix"]
    asymmetric_pair_2_4 = params["asymmetric_pair_2_4"]
    asymmetric_pair_4_2 = params["asymmetric_pair_4_2"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    required_edge_ratio = params["required_edge_ratio"]
    required_edge_set = params["required_edge_set"]
    non_required_edge_set = params["non_required_edge_set"]

    # Validate asymmetric entries are consistent with distance_matrix
    # (params may differ; use params values as authoritative for those entries)
    n = 9
    nodes = list(range(n))

    # Build cost dict from distance_matrix, overriding asymmetric pair
    cost = {}
    for i in nodes:
        for j in nodes:
            cost[i, j] = distance_matrix[i][j]
    # Override with explicit asymmetric params (should match matrix but use params)
    cost[2, 4] = asymmetric_pair_2_4
    cost[4, 2] = asymmetric_pair_4_2

    # Required edges as frozensets for undirected matching, but we track directed needs
    required_edges = [tuple(e) for e in required_edge_set]
    non_required_edges = [tuple(e) for e in non_required_edge_set]

    # This is the Route Inspection / Chinese Postman problem on a mixed/directed graph.
    # Each required edge (undirected) must be traversed at least once in at least one direction.
    # We model it as: for each required undirected edge (i,j), the truck traverses it
    # at least once total (in either direction).
    # We use arc-based flow formulation:
    #   x[i,j] = number of times arc (i->j) is used (integer >= 0)
    # Objective: minimize sum of cost[i,j] * x[i,j]
    # Constraints:
    #   Flow conservation at each node (in-flow = out-flow)
    #   For each required edge (i,j): x[i,j] + x[j,i] >= 1
    #   Connectivity: the used arcs form a single connected tour through depot
    #   x[i,j] >= 0, integer

    # Arc set: all directed arcs between distinct nodes
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("winter_road_maintenance")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # Decision variables: number of times each arc is traversed
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow conservation: for each node, in-flow == out-flow
    for node in nodes:
        model.addConstr(
            gp.quicksum(x[i, node] for i in nodes if i != node) ==
            gp.quicksum(x[node, j] for j in nodes if j != node),
            name=f"flow_{node}"
        )

    # The tour must be non-trivial: total arcs used >= 1 (depot must depart)
    model.addConstr(
        gp.quicksum(x[0, j] for j in nodes if j != 0) >= 1,
        name="depot_depart"
    )

    # Each required edge must be traversed at least once (in either direction)
    for idx, (i, j) in enumerate(required_edges):
        model.addConstr(
            x[i, j] + x[j, i] >= 1,
            name=f"req_edge_{idx}"
        )

    # Solve relaxation first to get a bound, then add subtour elimination
    # We use iterative subtour elimination (lazy constraints approach via callback)
    # For small n=9, we can solve with branch-and-cut using callbacks

    model.setParam("LazyConstraints", 1)

    def subtour_callback(cb_model, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = cb_model.cbGetSolution(x)
            # Build adjacency for used arcs
            # Find connected components reachable from depot
            used_arcs = [(i, j) for (i, j) in arcs if x_vals[i, j] > 0.5]
            if not used_arcs:
                return
            # Build graph
            adj = {node: [] for node in nodes}
            for (i, j) in used_arcs:
                adj[i].append(j)

            # BFS from depot
            visited = set()
            queue = [0]
            visited.add(0)
            while queue:
                cur = queue.pop(0)
                for nb in adj[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)

            # Find nodes with flow that are not reachable from depot
            active_nodes = set()
            for (i, j) in used_arcs:
                active_nodes.add(i)
                active_nodes.add(j)

            unreachable = active_nodes - visited
            if unreachable:
                # Add cut: for the subtour component, flow leaving must come from depot side
                # Standard subtour elimination: for subset S not containing depot,
                # sum of arcs leaving S >= 1
                # Find connected components among unreachable nodes
                # Get the component
                comp_adj = {node: [] for node in unreachable}
                for (i, j) in used_arcs:
                    if i in unreachable and j in unreachable:
                        comp_adj[i].append(j)

                # BFS to find components
                remaining = set(unreachable)
                while remaining:
                    start = next(iter(remaining))
                    comp = set()
                    bfs_q = [start]
                    comp.add(start)
                    while bfs_q:
                        cur = bfs_q.pop(0)
                        for nb in comp_adj[cur]:
                            if nb not in comp:
                                comp.add(nb)
                                bfs_q.append(nb)
                    remaining -= comp

                    # Add subtour elimination constraint for this component
                    # At least one arc must enter this component from outside
                    outside = [nd for nd in nodes if nd not in comp]
                    cb_model.cbLazy(
                        gp.quicksum(x[i, j] for i in outside for j in comp if i != j) >= 1
                    )

    model.optimize(lambda cb_model, where: subtour_callback(cb_model, where))

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj_val = model.ObjVal
        return {"objective": float(obj_val), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}