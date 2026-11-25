import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
import itertools


def solve(params):
    # ---- read parameters ----
    seg_demands = {
        (0, 2): params["demand_0_2"],
        (0, 6): params["demand_0_6"],
        (2, 3): params["demand_2_3"],
        (2, 4): params["demand_2_4"],
    }
    capacity = params["truck_capacity"]
    num_trucks = int(params["num_trucks"])
    num_nodes = int(params["num_nodes"])
    dist = params["distance_matrix"]

    segments = list(seg_demands.keys())
    trucks = list(range(num_trucks))
    num_segs = len(segments)

    # Convert flat/symmetric distance matrix into dict accessor
    def D(a, b):
        return dist[a * num_nodes + b]

    # Helper: best depot route servicing a set of segments (undirected edges),
    # starting and ending at depot 0, each segment traversed once (either direction).
    def route_cost_for_segments(seg_list):
        if not seg_list:
            return 0.0
        best = float("inf")
        for perm in itertools.permutations(range(len(seg_list))):
            for dirs in itertools.product([0, 1], repeat=len(seg_list)):
                cost = 0.0
                cur = 0
                for idx, d in zip(perm, dirs):
                    u, v = seg_list[idx]
                    if d == 1:
                        u, v = v, u
                    cost += D(cur, u) + D(u, v)
                    cur = v
                cost += D(cur, 0)
                if cost < best:
                    best = cost
        return best

    # Enumerate all nonempty subsets of segments, keep only feasible-by-capacity ones.
    # Map each feasible subset to an integer id.
    subset_costs = {}
    subset_segs = {}
    sid = 0
    for r in range(1, num_segs + 1):
        for combo in itertools.combinations(range(num_segs), r):
            total_dem = sum(seg_demands[segments[i]] for i in combo)
            if total_dem <= capacity:
                seg_list = [segments[i] for i in combo]
                subset_costs[sid] = route_cost_for_segments(seg_list)
                subset_segs[sid] = set(combo)
                sid += 1

    # Ensure every segment can be covered by some feasible subset
    covered_check = set()
    for s_id in subset_segs:
        covered_check.update(subset_segs[s_id])
    if covered_check != set(range(num_segs)):
        return {"objective": None, "status": "infeasible"}

    # ---- Build Pyomo model ----
    model = pyo.ConcreteModel()

    model.TRUCKS = pyo.Set(initialize=trucks, ordered=True)
    model.SUBSET_IDS = pyo.Set(initialize=list(subset_costs.keys()), ordered=True)

    model.x = pyo.Var(model.TRUCKS, model.SUBSET_IDS, domain=pyo.Binary)

    # Each truck chooses at most one subset
    def truck_one_rule(m, t):
        return sum(m.x[t, s] for s in m.SUBSET_IDS) <= 1
    model.truck_one = pyo.Constraint(model.TRUCKS, rule=truck_one_rule)

    # Each segment covered exactly once
    def seg_cover_rule(m, seg_idx):
        return sum(
            m.x[t, s]
            for t in m.TRUCKS
            for s in m.SUBSET_IDS
            if seg_idx in subset_segs[s]
        ) == 1
    model.seg_cover = pyo.Constraint(range(num_segs), rule=seg_cover_rule)

    # Objective: total travel distance over selected subsets
    model.total_cost = pyo.Objective(
        expr=sum(
            subset_costs[s] * model.x[t, s]
            for t in model.TRUCKS
            for s in model.SUBSET_IDS
        ),
        sense=pyo.minimize,
    )

    # ---- Solve ----
    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}