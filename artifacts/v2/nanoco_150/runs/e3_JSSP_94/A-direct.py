import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = ["J0", "J1", "J2"]
    ops = {
        "J0": [("M1", params["cycle_time_J0_M1"]),
               ("M0", params["cycle_time_J0_M0"]),
               ("M2", params["cycle_time_J0_M2"])],
        "J1": [("M1", params["cycle_time_J1_M1"]),
               ("M2", params["cycle_time_J1_M2"]),
               ("M0", params["cycle_time_J1_M0"])],
        "J2": [("M1", params["cycle_time_J2_M1"]),
               ("M0", params["cycle_time_J2_M0"]),
               ("M2", params["cycle_time_J2_M2"])],
    }

    # operation index pairs
    op_keys = [(j, k) for j in jobs for k in range(len(ops[j]))]
    machines = ["M0", "M1", "M2"]

    # map machine -> list of ops
    machine_ops = {mach: [] for mach in machines}
    for j in jobs:
        for k in range(len(ops[j])):
            machine_ops[ops[j][k][0]].append((j, k))

    model = pyo.ConcreteModel()

    model.OP = pyo.Set(initialize=op_keys, dimen=2)

    M_horizon = sum(ct for j in jobs for (_, ct) in ops[j])

    model.start = pyo.Var(model.OP, within=pyo.NonNegativeReals)
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    model.prec = pyo.ConstraintList()
    for j in jobs:
        for k in range(len(ops[j]) - 1):
            dur = ops[j][k][1]
            model.prec.add(model.start[j, k + 1] >= model.start[j, k] + dur)

    def cmax_rule(mdl, j):
        last = len(ops[j]) - 1
        dur = ops[j][last][1]
        return mdl.Cmax >= mdl.start[j, last] + dur
    model.cmax_con = pyo.Constraint(jobs, rule=cmax_rule)

    # disjunctive constraints per machine
    model.disj = pyo.ConstraintList()
    for mach in machines:
        lst = machine_ops[mach]
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                o1 = lst[a]
                o2 = lst[b]
                d1 = ops[o1[0]][o1[1]][1]
                d2 = ops[o2[0]][o2[1]][1]
                y = pyo.Var(within=pyo.Binary)
                setattr(model, f"y_{mach}_{a}_{b}", y)
                big = M_horizon
                model.disj.add(
                    model.start[o1] + d1 <= model.start[o2] + big * (1 - y)
                )
                model.disj.add(
                    model.start[o2] + d2 <= model.start[o1] + big * y
                )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}