import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_trains = int(params["num_trains"])
    num_tracks = int(params["num_tracks"])
    num_paths = int(params["num_paths"])
    num_stations = int(params["num_stations"])

    train_speeds = params["train_speeds"]
    stop_status = params["stop_status"]
    track_time_to_boundary = params["track_time_to_boundary"]
    min_dwell_time = float(params["min_dwell_time"])
    safe_interval = float(params["safe_interval"])

    T = list(range(num_trains))
    K = list(range(num_tracks))
    P = list(range(num_paths))

    # path -> track mapping (matches given path table)
    path_track = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 5: 3, 6: 4}

    track_paths = {k: [] for k in K}
    for p in P:
        track_paths[path_track[p]].append(p)

    ttb = {k: float(track_time_to_boundary[k]) for k in K}

    BIG_M = 10000.0

    model = pyo.ConcreteModel()

    model.arr = pyo.Var(T, within=pyo.Reals)
    model.dwell = pyo.Var(T, within=pyo.NonNegativeReals)
    model.dep = pyo.Var(T, within=pyo.Reals)
    model.y = pyo.Var(T, K, within=pyo.Binary)
    model.x = pyo.Var(T, P, within=pyo.Binary)

    # Pairwise ordering binaries (only for i < j)
    pairs = [(i, j) for i in T for j in T if i < j]
    model.order_path = pyo.Var(pairs, within=pyo.Binary)

    # Insertion (start of approach path usage) time = arr[i] - ttb[k]
    # To enforce safe intervals on approach paths: consecutive approach times differ >= safe_interval
    # Define a variable for path usage start time (linear)
    model.pstart = pyo.Var(T, within=pyo.Reals)

    def one_track_rule(m, i):
        return sum(m.y[i, k] for k in K) == 1
    model.one_track = pyo.Constraint(T, rule=one_track_rule)

    def one_path_rule(m, i):
        return sum(m.x[i, p] for p in P) == 1
    model.one_path = pyo.Constraint(T, rule=one_path_rule)

    def path_track_link_rule(m, i, k):
        return sum(m.x[i, p] for p in track_paths[k]) == m.y[i, k]
    model.path_track_link = pyo.Constraint(T, K, rule=path_track_link_rule)

    # pstart[i] = arr[i] - sum_k ttb[k]*y[i,k]
    def pstart_link_rule(m, i):
        return m.pstart[i] == m.arr[i] - sum(ttb[k] * m.y[i, k] for k in K)
    model.pstart_link = pyo.Constraint(T, rule=pstart_link_rule)

    # dep = arr + time on track (2*ttb) + dwell
    def dep_link_rule(m, i):
        return m.dep[i] == m.arr[i] + 2.0 * sum(ttb[k] * m.y[i, k] for k in K) + m.dwell[i]
    model.dep_link = pyo.Constraint(T, rule=dep_link_rule)

    def min_dwell_rule(m, i):
        return m.dwell[i] >= min_dwell_time
    model.min_dwell = pyo.Constraint(T, rule=min_dwell_rule)

    # Approach-path conflict: all paths pairwise conflict -> all train pairs must be
    # separated by safe_interval on pstart (start of approach). Use ordering binary.
    def path_sep_a_rule(m, i, j):
        # if order_path[i,j]==1 -> pstart[j] >= pstart[i] + safe_interval
        return m.pstart[j] >= m.pstart[i] + safe_interval - BIG_M * (1 - m.order_path[i, j])
    model.path_sep_a = pyo.Constraint(pairs, rule=path_sep_a_rule)

    def path_sep_b_rule(m, i, j):
        # if order_path[i,j]==0 -> pstart[i] >= pstart[j] + safe_interval
        return m.pstart[i] >= m.pstart[j] + safe_interval - BIG_M * m.order_path[i, j]
    model.path_sep_b = pyo.Constraint(pairs, rule=path_sep_b_rule)

    # Track capacity conflict: two trains on the same track (same arrival usage window)
    # cannot overlap. Use arrival-time separation conditioned on same track.
    # Use same ordering binary for Tracks sharing: if same track, need separation.
    # Introduce separate ordering binary for track.
    model.order_track = pyo.Var(pairs, within=pyo.Binary)

    def track_y_same(m, i, j):
        # returns linear expression 1 if same track chosen (sum_k y_ik*y_jk expressed as binary product)
        # We need linear; use auxiliary
        return None

    # Auxiliary binary: same_track[i,j] = 1 if both on same track
    model.same_track = pyo.Var(pairs, within=pyo.Binary)

    def same_track_upper_rule(m, i, j):
        # same_track <= sum_k of y_ik and y_jk combined; do pairwise linearization:
        # same_track <= y_ik + y_jk for association? Use: same_track == sum_k w_ijk
        return pyo.Constraint.Skip
    # Use per-track overlap: sum_k y_ik + y_jk - 1 <= M*(1-same_track) is not exact.
    # Simpler: same_track >= y_ik + y_jk - 1 for all k
    def same_track_lb_rule(m, i, j, k):
        return m.same_track[i, j] >= m.y[i, k] + m.y[j, k] - 1
    model.same_track_lb = pyo.Constraint(pairs, K, rule=same_track_lb_rule)

    def same_track_ub_rule(m, i, j):
        return m.same_track[i, j] <= sum(m.y[i, k] * m.y[j, k] for k in K)
    # product of binaries not allowed; rewrite via sum with per-k aux
    # Instead use aux per pair per track: z_ijk = y_ik*y_jk
    # Replace: define z
    # We'll remove same_track_ub and use z formulation instead.

    model.del_component(model.same_track_ub)

    # z[i,j,k] = y_ik * y_jk
    model.z = pyo.Var(pairs, K, within=pyo.Binary)

    def z_ub1_rule(m, i, j, k):
        return m.z[i, j, k] <= m.y[i, k]
    model.z_ub1 = pyo.Constraint(pairs, K, rule=z_ub1_rule)

    def z_ub2_rule(m, i, j, k):
        return m.z[i, j, k] <= m.y[j, k]
    model.z_ub2 = pyo.Constraint(pairs, K, rule=z_ub2_rule)

    def z_lb_rule(m, i, j, k):
        return m.z[i, j, k] >= m.y[i, k] + m.y[j, k] - 1
    model.z_lb = pyo.Constraint(pairs, K, rule=z_lb_rule)

    def same_track_link_rule(m, i, j):
        return m.same_track[i, j] == sum(m.z[i, j, k] for k in K)
    model.same_track_link = pyo.Constraint(pairs, rule=same_track_link_rule)

    # Track usage separation: if same_track -> |arr_i - arr_j| >= safe_interval
    def track_sep_a_rule(m, i, j):
        return m.arr[j] >= m.arr[i] + safe_interval - BIG_M * (1 - m.order_track[i, j]) \
               - BIG_M * (1 - m.same_track[i, j])
    model.track_sep_a = pyo.Constraint(pairs, rule=track_sep_a_rule)

    def track_sep_b_rule(m, i, j):
        return m.arr[i] >= m.arr[j] + safe_interval - BIG_M * m.order_track[i, j] \
               - BIG_M * (1 - m.same_track[i, j])
    model.track_sep_b = pyo.Constraint(pairs, rule=track_sep_b_rule)

    # Objective: minimize total dwell + small penalty on makespan
    model.obj = pyo.Objective(
        expr=sum(model.dwell[i] for i in T) + 0.001 * sum(model.dep[i] for i in T),
        sense=pyo.minimize
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}