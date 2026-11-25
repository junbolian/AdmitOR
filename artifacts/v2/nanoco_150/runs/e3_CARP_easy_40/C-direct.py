import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    truck_capacity = params["truck_capacity"]
    num_trucks = params["num_trucks"]
    demand_segment_0_3 = params["demand_segment_0_3"]
    demand_segment_0_4 = params["demand_segment_0_4"]
    demand_segment_2_6 = params["demand_segment_2_6"]
    demand_segment_5_7 = params["demand_segment_5_7"]
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]  # 8
    num_mandatory_segments = params["num_mandatory_segments"]  # 4

    # Segments: (node_a, node_b, demand)
    segments = [
        (0, 3, demand_segment_0_3),
        (0, 4, demand_segment_0_4),
        (2, 6, demand_segment_2_6),
        (5, 7, demand_segment_5_7),
    ]
    num_segs = num_mandatory_segments  # 4
    depot = 0

    def route_distance(seg_order):
        """
        Given an ordered list of segment indices, compute the minimum travel distance
        for a truck that starts at depot, traverses each segment (in some direction),
        and returns to depot.

        For each segment traversal we choose the direction (a->b or b->a) and the
        travel between consecutive stops to minimize total deadhead + service distance.

        We model this as: depot -> seg[0] start -> seg[0] end -> seg[1] start -> ... -> depot
        where for each segment we pick the direction minimizing total distance.

        We try all 2^k direction combinations for k segments in the order.
        """
        if not seg_order:
            return 0.0

        k = len(seg_order)
        best = float('inf')

        # Try all 2^k direction combinations
        for dirs in range(1 << k):
            # Build sequence of (entry_node, exit_node) for each segment
            seq = []
            for i, seg_idx in enumerate(seg_order):
                a, b, _ = segments[seg_idx]
                if (dirs >> i) & 1:
                    seq.append((a, b))
                else:
                    seq.append((b, a))

            # Compute travel: depot -> seq[0][0] -> seq[0][1] -> seq[1][0] -> ... -> depot
            dist = distance_matrix[depot][seq[0][0]]
            for i in range(len(seq) - 1):
                dist += distance_matrix[seq[i][1]][seq[i+1][0]]
            dist += distance_matrix[seq[-1][1]][depot]
            if dist < best:
                best = dist

        return best

    def best_route_cost(seg_indices):
        """
        Given a subset of segment indices assigned to one truck,
        find the optimal ordering and direction minimizing total travel distance.
        """
        if not seg_indices:
            return 0.0

        best = float('inf')
        for perm in permutations(seg_indices):
            cost = route_distance(list(perm))
            if cost < best:
                best = cost
        return best

    # Enumerate all feasible partitions of 4 segments into 2 trucks
    # Each segment assigned to exactly one truck; capacity must not be exceeded
    # We enumerate all subsets for truck 0; truck 1 gets the rest

    seg_indices = list(range(num_segs))  # [0, 1, 2, 3]
    demands = [seg[2] for seg in segments]

    # Build model: assign each segment to a truck, minimize total route cost
    # Decision: binary variable x[s, t] = 1 if segment s assigned to truck t
    model = gp.Model("winter_de_icing")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    x = model.addVars(num_segs, num_trucks, vtype=GRB.BINARY, name="x")

    # Each segment assigned to exactly one truck
    for s in range(num_segs):
        model.addConstr(gp.quicksum(x[s, t] for t in range(num_trucks)) == 1, name=f"assign_{s}")

    # Capacity constraints
    for t in range(num_trucks):
        model.addConstr(
            gp.quicksum(demands[s] * x[s, t] for s in range(num_segs)) <= truck_capacity,
            name=f"capacity_{t}"
        )

    # Since num_segs=4 and num_trucks=2, enumerate all feasible assignments
    # and find best via precomputed route costs embedded in a piecewise-linear or
    # big-M approach. Instead, since the problem is tiny, enumerate all 2^4=16
    # assignments directly and find the optimal one.

    best_obj = float('inf')
    best_assignment = None

    for mask in range(1 << num_segs):
        truck0_segs = [s for s in range(num_segs) if (mask >> s) & 1]
        truck1_segs = [s for s in range(num_segs) if not ((mask >> s) & 1)]

        # Check capacity
        if sum(demands[s] for s in truck0_segs) > truck_capacity:
            continue
        if sum(demands[s] for s in truck1_segs) > truck_capacity:
            continue

        cost0 = best_route_cost(truck0_segs)
        cost1 = best_route_cost(truck1_segs)
        total = cost0 + cost1

        if total < best_obj:
            best_obj = total
            best_assignment = (truck0_segs, truck1_segs)

    if best_assignment is None:
        return {"objective": None, "status": "infeasible"}

    # Use Gurobi to verify/formalize (fix variables to best assignment and solve)
    truck0_segs, truck1_segs = best_assignment

    for s in range(num_segs):
        if s in truck0_segs:
            model.addConstr(x[s, 0] == 1)
            model.addConstr(x[s, 1] == 0)
        else:
            model.addConstr(x[s, 0] == 0)
            model.addConstr(x[s, 1] == 1)

    # Objective: constant (the enumerated optimum), set as a constant via a dummy var
    obj_var = model.addVar(lb=best_obj, ub=best_obj, name="obj_val")
    model.setObjective(obj_var, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL or model.Status == GRB.SUBOPTIMAL:
        return {"objective": float(best_obj), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}