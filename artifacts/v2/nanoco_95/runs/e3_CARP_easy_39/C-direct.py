import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    num_trucks = int(params["num_trucks"])
    num_required_segments = int(params["num_required_segments"])
    truck_capacity = params["truck_capacity"]
    demand_segment_0_2 = params["demand_segment_0_2"]
    demand_segment_0_6 = params["demand_segment_0_6"]
    demand_segment_2_3 = params["demand_segment_2_3"]
    demand_segment_2_4 = params["demand_segment_2_4"]
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]
    dist = params["distance_matrix"]

    # Required segments with their demands (undirected)
    required_segments = [
        (0, 2, demand_segment_0_2),
        (0, 6, demand_segment_0_6),
        (2, 3, demand_segment_2_3),
        (2, 4, demand_segment_2_4),
    ]
    num_segs = len(required_segments)
    segments = list(range(num_segs))
    trucks = list(range(num_trucks))

    # Enumerate all feasible subsets of segments for each truck
    # A subset is feasible if total demand <= truck_capacity
    # For each feasible subset, compute the minimum travel cost (TSP on that subset)
    # starting and ending at depot 0.

    depot = 0

    def route_cost(seg_subset):
        """
        Compute minimum travel distance for a truck visiting all segments
        in seg_subset, starting and ending at depot 0.
        Each segment (i,j) must be traversed (in either direction).
        This is a Route Inspection / Rural Postman subproblem.
        We enumerate all orderings and directions of the segments.
        """
        if not seg_subset:
            return 0.0

        # Build list of segment endpoints with demands
        segs = [required_segments[s] for s in seg_subset]
        n = len(segs)

        # For each segment, we can traverse it as (i->j) or (j->i)
        # We need to find the optimal sequence visiting all segments,
        # starting from depot, possibly deadheading between segments.
        # State: current position, set of visited segments, direction chosen.
        # Use DP over subsets.

        # directions: 0 = traverse u->v, 1 = traverse v->u
        # For segment k: endpoints are segs[k][0] (u) and segs[k][1] (v)
        # Traversing u->v: enter at u, exit at v
        # Traversing v->u: enter at v, exit at u

        # DP: dp[mask][k][d] = min cost to have visited segments in mask,
        #     last segment was k, traversed in direction d (0: u->v, 1: v->u)
        # Start: at depot, no segments visited
        # Transition: from current exit node, deadhead to entry of next segment, traverse it

        INF = float('inf')
        # mask is bitmask over n segments
        size = 1 << n
        dp = [[[INF, INF] for _ in range(n)] for _ in range(size)]

        # Initialize: start from depot, go to first segment
        for k in range(n):
            u, v, _ = segs[k]
            # Direction 0: depot -> u, traverse u->v
            cost0 = dist[depot][u] + dist[u][v]
            dp[1 << k][k][0] = cost0
            # Direction 1: depot -> v, traverse v->u
            cost1 = dist[depot][v] + dist[v][u]
            dp[1 << k][k][1] = cost1

        for mask in range(1, size):
            for k in range(n):
                for d in range(2):
                    cur = dp[mask][k][d]
                    if cur == INF:
                        continue
                    # Exit node of segment k in direction d
                    u_k, v_k, _ = segs[k]
                    exit_node = v_k if d == 0 else u_k
                    # Try going to next unvisited segment
                    for nxt in range(n):
                        if mask & (1 << nxt):
                            continue
                        new_mask = mask | (1 << nxt)
                        u_n, v_n, _ = segs[nxt]
                        # Direction 0: deadhead exit_node -> u_n, traverse u_n->v_n
                        c0 = cur + dist[exit_node][u_n] + dist[u_n][v_n]
                        if c0 < dp[new_mask][nxt][0]:
                            dp[new_mask][nxt][0] = c0
                        # Direction 1: deadhead exit_node -> v_n, traverse v_n->u_n
                        c1 = cur + dist[exit_node][v_n] + dist[v_n][u_n]
                        if c1 < dp[new_mask][nxt][1]:
                            dp[new_mask][nxt][1] = c1

        # Return to depot from last segment
        full_mask = size - 1
        best = INF
        for k in range(n):
            u_k, v_k, _ = segs[k]
            for d in range(2):
                cur = dp[full_mask][k][d]
                if cur == INF:
                    continue
                exit_node = v_k if d == 0 else u_k
                total = cur + dist[exit_node][depot]
                if total < best:
                    best = total
        return best

    # Enumerate all subsets of segments, check feasibility, compute cost
    # We need to partition all segments among trucks exactly.
    # Each segment assigned to exactly one truck.
    # With num_trucks=2 and 4 segments, enumerate all 2^4=16 assignments.

    # For each truck, precompute feasible subsets and their costs
    # subset encoded as frozenset of segment indices

    all_subsets = []
    for r in range(num_segs + 1):
        for combo in itertools.combinations(segments, r):
            subset = frozenset(combo)
            total_demand = sum(required_segments[s][2] for s in subset)
            if total_demand <= truck_capacity:
                cost = route_cost(list(subset))
                all_subsets.append((subset, total_demand, cost))

    # Build ILP: assign each segment to exactly one truck, minimize total cost
    # Variables: x[t][subset_idx] = 1 if truck t uses this subset
    # This is a set partition problem.
    # With 2 trucks and 4 segments, we can enumerate all partitions directly.

    # Build model
    model = gp.Model("mail_collection")
    model.setParam("OutputFlag", 0)

    # For each truck, create binary variables for each feasible subset
    # x[t][i] = 1 if truck t is assigned subset i
    subset_list = all_subsets  # list of (frozenset, demand, cost)
    num_subsets = len(subset_list)

    x = {}
    for t in trucks:
        for i in range(num_subsets):
            x[t, i] = model.addVar(vtype=GRB.BINARY, name=f"x_{t}_{i}")

    model.update()

    # Each truck uses exactly one subset
    for t in trucks:
        model.addConstr(
            gp.quicksum(x[t, i] for i in range(num_subsets)) == 1,
            name=f"one_subset_truck_{t}"
        )

    # Each segment covered exactly once across all trucks
    for s in segments:
        model.addConstr(
            gp.quicksum(
                x[t, i]
                for t in trucks
                for i in range(num_subsets)
                if s in subset_list[i][0]
            ) == 1,
            name=f"cover_seg_{s}"
        )

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(
            subset_list[i][2] * x[t, i]
            for t in trucks
            for i in range(num_subsets)
        ),
        GRB.MINIMIZE
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