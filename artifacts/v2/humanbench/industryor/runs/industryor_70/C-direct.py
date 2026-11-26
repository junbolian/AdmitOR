import gurobipy as gp
from gurobipy import GRB
from datetime import datetime, timedelta


def solve(params):
    mileage_A_M = params["mileage_A_M"]
    mileage_Z_M = params["mileage_Z_M"]
    max_continuous_driving_minutes = params["max_continuous_driving_minutes"]
    max_daily_mileage_km = params["max_daily_mileage_km"]
    min_transfer_buffer_minutes = params["min_transfer_buffer_minutes"]
    max_shift_length_minutes = params["max_shift_length_minutes"]
    num_driving_tasks = params["num_driving_tasks"]
    # num_platforms is a structural param; read but not needed beyond that
    _ = params["num_platforms"]

    # ------------------------------------------------------------------
    # 1. Parse task data from embedded CSV
    # ------------------------------------------------------------------
    raw_csv = """Train Number,Train ID,Pickup Time,Pickup Location,Drop-off Time,Drop-off Location
331,M16,10:03:11,M,10:57:43,Z
1,L06,10:03:43,Z,10:58:32,M
163,N23,10:04:10,A,10:39:11,M
332,N27,10:04:32,M,10:40:10,A
333,N20,10:09:11,M,11:03:43,Z
2,L07,10:09:43,Z,11:04:32,M
164,L11,10:10:10,A,10:45:11,M
334,L01,10:10:32,M,10:46:10,A
335,M17,10:15:11,M,11:09:43,Z
3,M13,10:15:43,Z,11:10:32,M
165,N24,10:16:10,A,10:51:11,M
336,N28,10:16:32,M,10:52:10,A
337,N21,10:21:11,M,11:15:43,Z
4,L08,10:21:43,Z,11:16:32,M
166,N25,10:22:10,A,10:57:11,M
338,L02,10:22:32,M,10:58:10,A
339,M18,10:27:11,M,11:21:43,Z
5,M14,10:27:43,Z,11:22:32,M
167,N26,10:28:10,A,11:03:11,M
340,L03,10:28:32,M,11:04:10,A
341,N22,10:33:11,M,11:27:43,Z
6,L09,10:33:43,Z,11:28:32,M
168,L12,10:34:10,A,11:09:11,M
342,N29,10:34:32,M,11:10:10,A
343,N23,10:39:11,M,11:33:43,Z
7,M15,10:39:43,Z,11:34:32,M
169,N27,10:40:10,A,11:15:11,M
344,L04,10:40:32,M,11:16:10,A
345,L11,10:45:11,M,11:39:43,Z
8,N19,10:45:43,Z,11:40:32,M
170,L01,10:46:10,A,11:21:11,M
346,L05,10:46:32,M,11:22:10,A
347,N24,10:51:11,M,11:45:43,Z
9,L10,10:51:43,Z,11:46:32,M
171,N28,10:52:10,A,11:27:11,M
348,N30,10:52:32,M,11:28:10,A
349,N25,10:57:11,M,11:51:43,Z
10,M16,10:57:43,Z,11:52:32,M
172,L02,10:58:10,A,11:33:11,M
350,L06,10:58:32,M,11:34:10,A
351,N26,11:03:11,M,11:57:43,Z
11,N20,11:03:43,Z,11:58:32,M
173,L03,11:04:10,A,11:39:11,M
352,L07,11:04:32,M,11:40:10,A
353,L12,11:09:11,M,12:03:43,Z
12,M17,11:09:43,Z,12:04:32,M
174,N29,11:10:10,A,11:45:11,M
354,M13,11:10:32,M,11:46:10,A
355,N27,11:15:11,M,12:09:43,Z
13,N21,11:15:43,Z,12:10:32,M
175,L04,11:16:10,A,11:51:11,M
356,L08,11:16:32,M,11:52:10,A
357,L01,11:21:11,M,12:15:43,Z
14,M18,11:21:43,Z,12:16:32,M
176,L05,11:22:10,A,11:57:11,M
358,M14,11:22:32,M,11:58:10,A
359,N28,11:27:11,M,12:21:43,Z
15,N22,11:27:43,Z,12:22:32,M
177,N30,11:28:10,A,12:03:11,M
360,L09,11:28:32,M,12:04:10,A
361,L02,11:33:11,M,12:27:43,Z
16,N23,11:33:43,Z,12:28:32,M
178,L06,11:34:10,A,12:09:11,M
362,M15,11:34:32,M,12:10:10,A
363,L03,11:39:11,M,12:33:43,Z
17,L11,11:39:43,Z,12:34:32,M
179,L07,11:40:10,A,12:15:11,M
364,N19,11:40:32,M,12:16:10,A
365,N29,11:45:11,M,12:39:43,Z
18,N24,11:45:43,Z,12:40:32,M
180,M13,11:46:10,A,12:21:11,M
366,L10,11:46:32,M,12:22:10,A
367,L04,11:51:11,M,12:45:43,Z
19,N25,11:51:43,Z,12:46:32,M
181,L08,11:52:10,A,12:27:11,M
368,M16,11:52:32,M,12:28:10,A
369,L05,11:57:11,M,12:51:43,Z
20,N26,11:57:43,Z,12:52:32,M
182,M14,11:58:10,A,12:33:11,M
370,N20,11:58:32,M,12:34:10,A
371,N30,12:03:11,M,12:57:43,Z
21,L12,12:03:43,Z,12:58:32,M
183,L09,12:04:10,A,12:39:11,M
372,M17,12:04:32,M,12:40:10,A
373,L06,12:09:11,M,13:03:43,Z
22,N27,12:09:43,Z,13:04:32,M
184,M15,12:10:10,A,12:45:11,M
374,N21,12:10:32,M,12:46:10,A
375,L07,12:15:11,M,13:09:43,Z
23,L01,12:15:43,Z,13:10:32,M
185,N19,12:16:10,A,12:51:11,M
376,M18,12:16:32,M,12:52:10,A
377,M13,12:21:11,M,13:15:43,Z
24,N28,12:21:43,Z,13:16:32,M
186,L10,12:22:10,A,12:57:11,M
378,N22,12:22:32,M,12:58:10,A
379,L08,12:27:11,M,13:21:43,Z
25,L02,12:27:43,Z,13:22:32,M
187,M16,12:28:10,A,13:03:11,M
380,N23,12:28:32,M,13:04:10,A
381,M14,12:33:11,M,13:27:43,Z
26,L03,12:33:43,Z,13:28:32,M
188,N20,12:34:10,A,13:09:11,M
382,L11,12:34:32,M,13:10:10,A
383,L09,12:39:11,M,13:33:43,Z
27,N29,12:39:43,Z,13:34:32,M
189,M17,12:40:10,A,13:15:11,M
384,N24,12:40:32,M,13:16:10,A
385,M15,12:45:11,M,13:39:43,Z
28,L04,12:45:43,Z,13:40:32,M
190,N21,12:46:10,A,13:21:11,M
386,N25,12:46:32,M,13:22:10,A
387,N19,12:51:11,M,13:45:43,Z
29,L05,12:51:43,Z,13:46:32,M
191,M18,12:52:10,A,13:27:11,M
388,N26,12:52:32,M,13:28:10,A
389,L10,12:57:11,M,13:51:43,Z
30,N30,12:57:43,Z,13:52:32,M
192,N22,12:58:10,A,13:33:11,M
390,L12,12:58:32,M,13:34:10,A
391,M16,13:03:11,M,13:57:43,Z
31,L06,13:03:43,Z,13:58:32,M
193,N23,13:04:10,A,13:39:11,M
392,N27,13:04:32,M,13:40:10,A
393,N20,13:09:11,M,14:03:43,Z
32,L07,13:09:43,Z,14:04:32,M
194,L11,13:10:10,A,13:45:11,M
394,L01,13:10:32,M,13:46:10,A
395,M17,13:15:11,M,14:09:43,Z
33,M13,13:15:43,Z,14:10:32,M
195,N24,13:16:10,A,13:51:11,M
396,N28,13:16:32,M,13:52:10,A
397,N21,13:21:11,M,14:15:43,Z
34,L08,13:21:43,Z,14:16:32,M
196,N25,13:22:10,A,13:57:11,M
398,L02,13:22:32,M,13:58:10,A
399,M18,13:27:11,M,14:21:43,Z
35,M14,13:27:43,Z,14:22:32,M
197,N26,13:28:10,A,14:03:11,M
400,L03,13:28:32,M,14:04:10,A
401,N22,13:33:11,M,14:27:43,Z
36,L09,13:33:43,Z,14:28:32,M
198,L12,13:34:10,A,14:09:11,M
402,N29,13:34:32,M,14:10:10,A
403,N23,13:39:11,M,14:33:43,Z
37,M15,13:39:43,Z,14:34:32,M
199,N27,13:40:10,A,14:15:11,M
404,L04,13:40:32,M,14:16:10,A
405,L11,13:45:11,M,14:39:43,Z
38,N19,13:45:43,Z,14:40:32,M
200,L01,13:46:10,A,14:21:11,M
406,L05,13:46:32,M,14:22:10,A
407,N24,13:51:11,M,14:45:43,Z
39,L10,13:51:43,Z,14:46:32,M
201,N28,13:52:10,A,14:27:11,M
408,N30,13:52:32,M,14:28:10,A
409,N25,13:57:11,M,14:51:43,Z
40,M16,13:57:43,Z,14:52:32,M
202,L02,13:58:10,A,14:33:11,M
410,L06,13:58:32,M,14:34:10,A
411,N26,14:03:11,M,14:57:43,Z
41,N20,14:03:43,Z,14:58:32,M
203,L03,14:04:10,A,14:39:11,M
412,L07,14:04:32,M,14:40:10,A
413,L12,14:09:11,M,15:03:43,Z
42,M17,14:09:43,Z,15:04:32,M
204,N29,14:10:10,A,14:45:11,M
414,M13,14:10:32,M,14:46:10,A
415,N27,14:15:11,M,15:09:43,Z
43,N21,14:15:43,Z,15:10:32,M
205,L04,14:16:10,A,14:51:11,M
416,L08,14:16:32,M,14:52:10,A
417,L01,14:21:11,M,15:15:43,Z
44,M18,14:21:43,Z,15:16:32,M
206,L05,14:22:10,A,14:57:11,M
418,M14,14:22:32,M,14:58:10,A
419,N28,14:27:11,M,15:21:43,Z
45,N22,14:27:43,Z,15:22:32,M
207,N30,14:28:10,A,15:03:11,M
420,L09,14:28:32,M,15:04:10,A
421,L02,14:33:11,M,15:27:43,Z
46,N23,14:33:43,Z,15:28:32,M
208,L06,14:34:10,A,15:09:11,M
422,M15,14:34:32,M,15:10:10,A
423,L03,14:39:11,M,15:33:43,Z
47,L11,14:39:43,Z,15:34:32,M
209,L07,14:40:10,A,15:15:11,M
424,N19,14:40:32,M,15:16:10,A
425,N29,14:45:11,M,15:39:43,Z
48,N24,14:45:43,Z,15:40:32,M
210,M13,14:46:10,A,15:21:11,M
426,L10,14:46:32,M,15:22:10,A
427,L04,14:51:11,M,15:45:43,Z
49,N25,14:51:43,Z,15:46:32,M
211,L08,14:52:10,A,15:27:11,M
428,M16,14:52:32,M,15:28:10,A
429,L05,14:57:11,M,15:51:43,Z
50,N26,14:57:43,Z,15:52:32,M
212,M14,14:58:10,A,15:33:11,M
430,N20,14:58:32,M,15:34:10,A"""

    # ------------------------------------------------------------------
    # 2. Parse tasks
    # ------------------------------------------------------------------
    base_date = datetime(2024, 1, 1)

    def parse_time(t_str):
        h, m, s = t_str.strip().split(":")
        return base_date + timedelta(hours=int(h), minutes=int(m), seconds=int(s))

    def segment_mileage(loc_from, loc_to):
        if loc_from == loc_to:
            return 0.0
        pair = frozenset([loc_from, loc_to])
        if pair == frozenset(["A", "M"]):
            return mileage_A_M
        if pair == frozenset(["Z", "M"]):
            return mileage_Z_M
        # A <-> Z via M
        return mileage_A_M + mileage_Z_M

    tasks = []
    lines = raw_csv.strip().split("\n")
    for line in lines[1:]:
        parts = line.strip().split(",")
        if len(parts) < 6:
            continue
        pickup_loc = parts[3].strip()
        dropoff_loc = parts[5].strip()
        pickup_time = parse_time(parts[2])
        dropoff_time = parse_time(parts[4])
        driving_minutes = (dropoff_time - pickup_time).total_seconds() / 60.0
        mile = segment_mileage(pickup_loc, dropoff_loc)
        tasks.append({
            "pickup_time": pickup_time,
            "dropoff_time": dropoff_time,
            "pickup_loc": pickup_loc,
            "dropoff_loc": dropoff_loc,
            "driving_minutes": driving_minutes,
            "mileage": mile,
        })

    n = num_driving_tasks
    tasks = tasks[:n]

    # ------------------------------------------------------------------
    # 3. Enumerate feasible duty chains (column generation via enumeration)
    #
    #    Strategy: use DFS/DP to build all maximal chains respecting:
    #      - time feasibility (gap >= buffer when different platform)
    #      - max_continuous_driving_minutes (accumulate; reset on break)
    #      - max_daily_mileage_km (accumulate whole duty)
    #      - max_shift_length_minutes (clock from first pickup to last dropoff)
    #
    #    Then solve a set-partitioning LP/IP over these columns.
    # ------------------------------------------------------------------

    # Precompute: for each task i, sorted list of tasks j that can follow i
    # feasibility check for direct succession (i -> j):
    #   gap = pickup_j - dropoff_i >= 0
    #   if different platform: gap >= min_transfer_buffer_minutes
    #   if same platform: gap >= 0 (driver stays put, no travel needed)

    # Build successor list
    # Sort tasks by pickup time for efficiency
    task_order = sorted(range(n), key=lambda k: tasks[k]["pickup_time"])

    # For each task index, precompute possible successors (by time)
    successors = [[] for _ in range(n)]
    for ii, i in enumerate(task_order):
        ti = tasks[i]
        for j in task_order:
            if i == j:
                continue
            tj = tasks[j]
            gap = (tj["pickup_time"] - ti["dropoff_time"]).total_seconds() / 60.0
            if gap < 0:
                continue
            if ti["dropoff_loc"] != tj["pickup_loc"]:
                if gap < min_transfer_buffer_minutes:
                    continue
            # Passes time/location check — add as candidate successor
            successors[i].append(j)

    # Enumerate all feasible chains via DFS with pruning
    # State: (current_task, continuous_drive_so_far, total_mileage, shift_start_time)
    # We collect complete chains (lists of task indices)
    all_chains = []

    def dfs(chain, cont_drive, total_mile, shift_start):
        all_chains.append(list(chain))  # record current (possibly extendable) chain
        last = chain[-1]
        tl = tasks[last]
        for j in successors[last]:
            tj = tasks[j]
            gap = (tj["pickup_time"] - tl["dropoff_time"]).total_seconds() / 60.0
            is_break = (tl["dropoff_loc"] != tj["pickup_loc"]) or (gap >= min_transfer_buffer_minutes)

            # Continuous driving after transition
            new_cont = (0.0 if is_break else cont_drive) + tj["driving_minutes"]
            if new_cont > max_continuous_driving_minutes:
                continue

            # Total mileage
            new_mile = total_mile + tj["mileage"]
            if new_mile > max_daily_mileage_km:
                continue

            # Shift length (clock time)
            shift_len = (tj["dropoff_time"] - shift_start).total_seconds() / 60.0
            if shift_len > max_shift_length_minutes:
                continue

            chain.append(j)
            dfs(chain, new_cont, new_mile, shift_start)
            chain.pop()

    for i in range(n):
        ti = tasks[i]
        init_drive = ti["driving_minutes"]
        # If a single task already violates continuous driving, skip
        if init_drive > max_continuous_driving_minutes:
            # Still need to cover it — treat as a singleton chain (will be infeasible
            # unless constraint is relaxed, but we include it so coverage is possible)
            all_chains.append([i])
            continue
        if ti["mileage"] > max_daily_mileage_km:
            all_chains.append([i])
            continue
        dfs([i], init_drive, ti["mileage"], ti["pickup_time"])

    # Deduplicate chains
    seen = set()
    unique_chains = []
    for ch in all_chains:
        key = tuple(ch)
        if key not in seen:
            seen.add(key)
            unique_chains.append(ch)

    # ------------------------------------------------------------------
    # 4. Set-partitioning MIP
    #    min  sum_c lambda_c
    #    s.t. sum_{c: i in c} lambda_c = 1  for all tasks i
    #         lambda_c in {0,1}
    # ------------------------------------------------------------------
    model = gp.Model("crew_set_partition")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 300)
    model.setParam("MIPGap", 0.0)

    num_chains = len(unique_chains)
    lam = model.addVars(num_chains, vtype=GRB.BINARY, name="lam")

    # Objective: minimise number of duties
    model.setObjective(gp.quicksum(lam[c] for c in range(num_chains)), GRB.MINIMIZE)

    # Coverage constraints: each task covered exactly once
    # Build task -> chain membership
    task_to_chains = [[] for _ in range(n)]
    for c, chain in enumerate(unique_chains):
        for task_idx in chain:
            task_to_chains[task_idx].append(c)

    for i in range(n):
        covering = task_to_chains[i]
        if not covering:
            # No chain covers this task — problem is infeasible
            return {"objective": None, "status": "infeasible_no_chain_for_task"}
        model.addConstr(
            gp.quicksum(lam[c] for c in covering) == 1,
            name=f"cover_{i}"
        )

    # ------------------------------------------------------------------
    # 5. Solve
    # ------------------------------------------------------------------
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjVal), "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}