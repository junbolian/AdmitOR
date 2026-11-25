import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pt = {}
    pt[(0, 0, 1)] = params["processing_time_B0_on_U1_stage1"]
    pt[(0, 1, 0)] = params["processing_time_B0_on_U0_stage2"]  # stage2 key says U0
    pt[(0, 2, 2)] = params["processing_time_B0_on_U2_stage3"]

    pt[(1, 0, 1)] = params["processing_time_B1_on_U1_stage1"]
    pt[(1, 1, 0)] = params["processing_time_B1_on_U0_stage2"]
    pt[(1, 2, 2)] = params["processing_time_B1_on_U2_stage3"]

    pt[(2, 0, 2)] = params["processing_time_B2_on_U2_stage1"]
    pt[(2, 1, 1)] = params["processing_time_B2_on_U1_stage2"]
    pt[(2, 2, 0)] = params["processing_time_B2_on_U0_stage3"]

    # Route: batch -> ordered list of (stage_index, unit)
    routes = {
        0: [(0, 1), (1, 0), (2, 2)],
        1: [(0, 1), (1, 0), (2, 2)],
        2: [(0, 2), (1, 1), (2, 0)],
    }

    batches = [0, 1, 2]
    units = [0, 1, 2]

    # Big-M: upper bound on makespan
    M = sum(pt.values())

    model = gp.Model("batch_scheduling")
    model.setParam("OutputFlag", 0)

    # Start time variables: s[b, s_idx] = start time of stage s_idx for batch b
    s = {}
    for b in batches:
        for (si, u) in routes[b]:
            s[(b, si)] = model.addVar(lb=0.0, name=f"s_b{b}_s{si}")

    # Makespan variable
    Cmax = model.addVar(lb=0.0, name="Cmax")

    model.setObjective(Cmax, GRB.MINIMIZE)

    # 1. Sequence constraints within each batch (stage precedence)
    for b in batches:
        route = routes[b]
        for k in range(len(route) - 1):
            si_curr, u_curr = route[k]
            si_next, u_next = route[k + 1]
            model.addConstr(
                s[(b, si_next)] >= s[(b, si_curr)] + pt[(b, si_curr, u_curr)],
                name=f"seq_b{b}_s{si_curr}_to_s{si_next}"
            )

    # 2. Makespan >= completion of every stage
    for b in batches:
        for (si, u) in routes[b]:
            model.addConstr(
                Cmax >= s[(b, si)] + pt[(b, si, u)],
                name=f"cmax_b{b}_s{si}"
            )

    # 3. No-overlap on each unit: for each pair of operations on the same unit,
    #    one must finish before the other starts.
    #    Binary variable y[(b1,si1,b2,si2)] = 1 means (b1,si1) precedes (b2,si2)
    y = {}
    # Collect all operations per unit
    unit_ops = {u: [] for u in units}
    for b in batches:
        for (si, u) in routes[b]:
            unit_ops[u].append((b, si))

    for u in units:
        ops = unit_ops[u]
        for idx1 in range(len(ops)):
            for idx2 in range(idx1 + 1, len(ops)):
                b1, si1 = ops[idx1]
                b2, si2 = ops[idx2]
                yvar = model.addVar(vtype=GRB.BINARY, name=f"y_b{b1}s{si1}_b{b2}s{si2}_u{u}")
                y[(b1, si1, b2, si2, u)] = yvar

                # (b1,si1) before (b2,si2)
                model.addConstr(
                    s[(b1, si1)] + pt[(b1, si1, u)] <= s[(b2, si2)] + M * (1 - yvar),
                    name=f"nooverlap1_b{b1}s{si1}_b{b2}s{si2}_u{u}"
                )
                # (b2,si2) before (b1,si1)
                model.addConstr(
                    s[(b2, si2)] + pt[(b2, si2, u)] <= s[(b1, si1)] + M * yvar,
                    name=f"nooverlap2_b{b1}s{si1}_b{b2}s{si2}_u{u}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(Cmax.X), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}