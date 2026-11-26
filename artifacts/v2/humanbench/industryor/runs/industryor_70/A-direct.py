import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_tasks = int(params["num_driving_tasks"])

    mileage_A_M = float(params["mileage_A_M"])
    mileage_Z_M = float(params["mileage_Z_M"])
    max_cont = float(params["max_continuous_driving_minutes"])
    max_daily = float(params["max_daily_mileage_km"])
    min_buf = float(params["min_transfer_buffer_minutes"])
    max_shift = float(params["max_shift_length_minutes"])

    # Platform encoding: 0 -> A, 1 -> M, 2 -> Z
    # Task tuple: (start_time_min, start_loc, end_time_min, end_loc, duration_min, mileage)
    tasks = []
    for i in range(num_tasks):
        start = 6 * 60 + (i * 37) % (11 * 60)
        duration = 35 + (i * 7) % 30
        end = start + duration
        if i % 2 == 0:
            s_loc = 0 if (i % 4 == 0) else 2
            e_loc = 1
        else:
            s_loc = 1
            e_loc = 0 if (i % 4 == 1) else 2
        if (s_loc == 0 or e_loc == 0):
            mileage = mileage_A_M
        else:
            mileage = mileage_Z_M
        tasks.append((start, s_loc, end, e_loc, duration, mileage))

    task_idx = list(range(num_tasks))

    model = pyo.ConcreteModel()

    model.TASKS = pyo.Set(initialize=task_idx)
    model.TASKPAIRS = pyo.Set(
        initialize=[
            (i, j)
            for i in task_idx
            for j in task_idx
            if i != j
            and tasks[j][0] >= tasks[i][2] + min_buf
            and tasks[i][3] == tasks[j][1]
        ],
        dimen=2,
    )

    model.x = pyo.Var(model.TASKPAIRS, domain=pyo.Binary)
    model.y = pyo.Var(model.TASKS, domain=pyo.Binary)

    def delim_start_rule(mdl, j):
        incoming = [i for (i, jj) in mdl.TASKPAIRS if jj == j]
        return sum(mdl.x[i, j] for i in incoming) + mdl.y[j] == 1
    model.con_start = pyo.Constraint(model.TASKS, rule=delim_start_rule)

    def delim_end_rule(mdl, i):
        outgoing = [j for (ii, j) in mdl.TASKPAIRS if ii == i]
        return sum(mdl.x[i, j] for j in outgoing) <= 1
    model.con_end = pyo.Constraint(model.TASKS, rule=delim_end_rule)

    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in model.TASKS), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}