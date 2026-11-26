import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    raw_len = params["raw_pipe_length"]
    demand = {
        290: params["demand_290"],
        315: params["demand_315"],
        350: params["demand_350"],
        455: params["demand_455"],
    }
    max_patterns = params["max_pattern_types"]
    max_pieces  = params["max_pieces_per_raw"]
    max_leftover = params["max_leftover"]
    ec = [
        params["extra_cost_fraction_most"],
        params["extra_cost_fraction_second"],
        params["extra_cost_fraction_third"],
        params["extra_cost_fraction_fourth"],
    ]
    sizes = [290, 315, 350, 455]

    # Enumerate all feasible patterns
    patterns = []
    for a in range(int(raw_len // 290) + 1):
        for b in range(int(raw_len // 315) + 1):
            for c in range(int(raw_len // 350) + 1):
                for d in range(int(raw_len // 455) + 1):
                    total_pieces = a + b + c + d
                    if total_pieces == 0:
                        continue
                    used = 290*a + 315*b + 350*c + 455*d
                    leftover = raw_len - used
                    if leftover < 0:
                        continue
                    if total_pieces > max_pieces:
                        continue
                    if leftover > max_leftover:
                        continue
                    patterns.append((a, b, c, d))

    P = len(patterns)
    if P == 0:
        return {"objective": None, "status": "no feasible patterns"}

    K = max_patterns  # number of rank slots = max_pattern_types
    # Big-M for ordering constraints
    total_demand = sum(demand.values())
    BigM = total_demand + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[p] = number of raw pipes cut with pattern p
    x = model.addVars(P, vtype=GRB.INTEGER, lb=0, name="x")
    # z[p] = 1 if pattern p is used at all
    z = model.addVars(P, vtype=GRB.BINARY, name="z")
    # r[p,k] = 1 if pattern p is assigned rank k (k=0 is most used)
    r = model.addVars(P, K, vtype=GRB.BINARY, name="r")
    # y[k] = number of pipes cut with the pattern of rank k
    y = model.addVars(K, vtype=GRB.INTEGER, lb=0, name="y")

    # Demand constraints
    for idx, sz in enumerate(sizes):
        model.addConstr(
            gp.quicksum(patterns[p][idx] * x[p] for p in range(P)) >= demand[sz],
            name=f"demand_{sz}"
        )

    # Link z to x: x[p] <= BigM * z[p]
    for p in range(P):
        model.addConstr(x[p] <= BigM * z[p], name=f"link_z_{p}")
        model.addConstr(x[p] >= z[p], name=f"link_z_lb_{p}")

    # At most max_patterns patterns used
    model.addConstr(gp.quicksum(z[p] for p in range(P)) <= K, name="max_patterns")

    # Each pattern assigned at most one rank
    for p in range(P):
        model.addConstr(gp.quicksum(r[p, k] for k in range(K)) <= 1, name=f"rank_assign_{p}")

    # r[p,k] can only be 1 if z[p]=1
    for p in range(P):
        for k in range(K):
            model.addConstr(r[p, k] <= z[p], name=f"rank_active_{p}_{k}")

    # Each rank slot assigned to exactly one pattern (only if that many patterns used)
    # We need exactly sum(z) patterns ranked, each rank k used exactly once if k < sum(z)
    # Simpler: each rank slot k gets at most one pattern
    for k in range(K):
        model.addConstr(gp.quicksum(r[p, k] for p in range(P)) <= 1, name=f"rank_slot_{k}")

    # Every used pattern must be assigned a rank
    for p in range(P):
        model.addConstr(
            gp.quicksum(r[p, k] for k in range(K)) >= z[p],
            name=f"rank_cover_{p}"
        )

    # y[k] = x[p] for the pattern p assigned rank k
    # y[k] = sum_p r[p,k] * x[p]  -- linearize with bilinear term
    # Introduce w[p,k] = r[p,k] * x[p]
    w = model.addVars(P, K, vtype=GRB.INTEGER, lb=0, name="w")
    for p in range(P):
        for k in range(K):
            # w[p,k] <= BigM * r[p,k]
            model.addConstr(w[p, k] <= BigM * r[p, k], name=f"w_ub_{p}_{k}")
            # w[p,k] <= x[p]
            model.addConstr(w[p, k] <= x[p], name=f"w_x_ub_{p}_{k}")
            # w[p,k] >= x[p] - BigM*(1 - r[p,k])
            model.addConstr(w[p, k] >= x[p] - BigM * (1 - r[p, k]), name=f"w_x_lb_{p}_{k}")

    for k in range(K):
        model.addConstr(y[k] == gp.quicksum(w[p, k] for p in range(P)), name=f"y_def_{k}")

    # Ordering: rank 0 >= rank 1 >= rank 2 >= rank 3 (most used first)
    for k in range(K - 1):
        model.addConstr(y[k] >= y[k + 1], name=f"order_{k}")

    # Total raw pipes used
    total_pipes = gp.quicksum(x[p] for p in range(P))

    # Extra cost = sum_k ec[k] * y[k]  (y[k] pipes at rank k each cost ec[k] extra)
    extra_cost = gp.quicksum(ec[k] * y[k] for k in range(K))

    # Objective: minimize total_pipes + extra_cost
    # (cost of raw pipes = total_pipes * 1, extra cost = extra_cost * 1 pipe-unit)
    model.setObjective(total_pipes + extra_cost, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}