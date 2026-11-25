import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]

    # Lots and machines
    lots = [0, 1, 2]       # L0, L1, L2
    steps = [0, 1, 2]      # step indices
    # Fixed routing: each lot goes M1 -> M0 -> M2
    routing = [1, 0, 2]    # routing[step] = machine index

    # p[lot][step] = processing time
    p = {
        lot: {step: processing_times[lot][step] for step in steps}
        for lot in lots
    }

    # Big-M: upper bound on makespan
    M_big = sum(processing_times[lot][step] for lot in lots for step in steps)

    model = gp.Model("wafer_fab_scheduling")
    model.setParam("OutputFlag", 0)

    # Start times: s[lot, step]
    s = model.addVars(lots, steps, lb=0.0, name="s")

    # Makespan
    Cmax = model.addVar(lb=0.0, name="Cmax")

    # Objective
    model.setObjective(Cmax, GRB.MINIMIZE)

    # Makespan >= completion of every lot's last step
    for lot in lots:
        model.addConstr(Cmax >= s[lot, 2] + p[lot][2], name=f"makespan_lot{lot}")

    # Technological ordering: each lot must finish step k before starting step k+1
    for lot in lots:
        for step in range(2):
            model.addConstr(
                s[lot, step + 1] >= s[lot, step] + p[lot][step],
                name=f"tech_order_lot{lot}_step{step}"
            )

    # No-overlap on each machine: for each pair of lots sharing the same machine at some step,
    # only one can go first.
    # y[i, si, j, sj] = 1 if lot i step si precedes lot j step sj on the same machine
    # We need this for each pair (i, step_i), (j, step_j) where routing[step_i] == routing[step_j]
    # and i != j (or same lot different steps on same machine — not possible here since routing visits
    # each machine exactly once per lot and all lots share the same routing)

    # Collect pairs of (lot, step) that use the same machine
    machine_ops = {}  # machine -> list of (lot, step)
    for lot in lots:
        for step in steps:
            mac = routing[step]
            if mac not in machine_ops:
                machine_ops[mac] = []
            machine_ops[mac].append((lot, step))

    # Binary variable: y[i, si, j, sj] = 1 means (lot i, step si) finishes before (lot j, step sj) starts
    y = {}
    for mac, ops in machine_ops.items():
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                lot_i, step_i = ops[idx_a]
                lot_j, step_j = ops[idx_b]
                key = (lot_i, step_i, lot_j, step_j)
                y[key] = model.addVar(vtype=GRB.BINARY, name=f"y_{lot_i}_{step_i}_{lot_j}_{step_j}")

    # No-overlap constraints
    for mac, ops in machine_ops.items():
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                lot_i, step_i = ops[idx_a]
                lot_j, step_j = ops[idx_b]
                key = (lot_i, step_i, lot_j, step_j)
                yv = y[key]
                # Either i before j, or j before i
                model.addConstr(
                    s[lot_j, step_j] >= s[lot_i, step_i] + p[lot_i][step_i] - M_big * (1 - yv),
                    name=f"no_overlap_fwd_{lot_i}_{step_i}_{lot_j}_{step_j}"
                )
                model.addConstr(
                    s[lot_i, step_i] >= s[lot_j, step_j] + p[lot_j][step_j] - M_big * yv,
                    name=f"no_overlap_bwd_{lot_i}_{step_i}_{lot_j}_{step_j}"
                )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}