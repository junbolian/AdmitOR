import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Jobs and their sequences: (machine, duration_param_key)
    # J0: M1 -> M0 -> M2
    # J1: M1 -> M2 -> M0
    # J2: M1 -> M0 -> M2

    jobs = {
        "J0": [
            (1, params["cycle_time_J0_M1"]),
            (0, params["cycle_time_J0_M0"]),
            (2, params["cycle_time_J0_M2"]),
        ],
        "J1": [
            (1, params["cycle_time_J1_M1"]),
            (2, params["cycle_time_J1_M2"]),
            (0, params["cycle_time_J1_M0"]),
        ],
        "J2": [
            (1, params["cycle_time_J2_M1"]),
            (0, params["cycle_time_J2_M0"]),
            (2, params["cycle_time_J2_M2"]),
        ],
    }

    job_names = ["J0", "J1", "J2"]
    num_steps = 3

    # Big-M: upper bound on makespan
    big_M = sum(
        d
        for jname in job_names
        for (_, d) in jobs[jname]
    )

    model = gp.Model("jobshop")
    model.setParam("OutputFlag", 0)

    # Start time variables: start[j][s] = start time of step s of job j
    start = {
        jname: [
            model.addVar(lb=0.0, name=f"start_{jname}_{s}")
            for s in range(num_steps)
        ]
        for jname in job_names
    }

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Objective: minimize makespan
    model.setObjective(makespan, GRB.MINIMIZE)

    # Precedence constraints within each job
    for jname in job_names:
        seq = jobs[jname]
        for s in range(num_steps - 1):
            _, dur = seq[s]
            model.addConstr(
                start[jname][s + 1] >= start[jname][s] + dur,
                name=f"prec_{jname}_{s}"
            )

    # Makespan >= completion of last step of each job
    for jname in job_names:
        last_machine, last_dur = jobs[jname][num_steps - 1]
        model.addConstr(
            makespan >= start[jname][num_steps - 1] + last_dur,
            name=f"mkspan_{jname}"
        )

    # No-overlap constraints on each machine
    # For each pair of operations on the same machine, one must precede the other
    # Collect all operations per machine: (job_name, step_index, duration)
    machine_ops = {0: [], 1: [], 2: []}
    for jname in job_names:
        for s, (mach, dur) in enumerate(jobs[jname]):
            machine_ops[mach].append((jname, s, dur))

    # Binary variable y[i][j] = 1 if operation i precedes operation j on same machine
    y = {}
    for mach in range(3):
        ops = machine_ops[mach]
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                jname_a, s_a, dur_a = ops[idx_a]
                jname_b, s_b, dur_b = ops[idx_b]
                var_name = f"y_{jname_a}_{s_a}_{jname_b}_{s_b}"
                y[(jname_a, s_a, jname_b, s_b)] = model.addVar(
                    vtype=GRB.BINARY, name=var_name
                )

    for mach in range(3):
        ops = machine_ops[mach]
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                jname_a, s_a, dur_a = ops[idx_a]
                jname_b, s_b, dur_b = ops[idx_b]
                yvar = y[(jname_a, s_a, jname_b, s_b)]

                # Either a finishes before b starts, or b finishes before a starts
                model.addConstr(
                    start[jname_a][s_a] + dur_a <= start[jname_b][s_b] + big_M * (1 - yvar),
                    name=f"nol1_m{mach}_{jname_a}{s_a}_{jname_b}{s_b}"
                )
                model.addConstr(
                    start[jname_b][s_b] + dur_b <= start[jname_a][s_a] + big_M * yvar,
                    name=f"nol2_m{mach}_{jname_a}{s_a}_{jname_b}{s_b}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}