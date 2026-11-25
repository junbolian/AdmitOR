import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proc_time = params["proc_time"]
    robot_assignment = params["robot_assignment"]

    num_tasks = len(proc_time)
    num_stages = len(proc_time[0])
    num_robots = 3

    big_M = sum(proc_time[t][s] for t in range(num_tasks) for s in range(num_stages))

    model = pyo.ConcreteModel()

    model.TASKS = pyo.RangeSet(0, num_tasks - 1)
    model.STAGES = pyo.RangeSet(0, num_stages - 1)

    # Start time of operation (task, stage)
    model.start = pyo.Var(model.TASKS, model.STAGES, within=pyo.NonNegativeReals)

    # Makespan
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)

    def completion_rule(m, t, s):
        return m.start[t, s] + proc_time[t][s] <= m.Cmax

    model.completion_con = pyo.Constraint(model.TASKS, model.STAGES, rule=completion_rule)

    # Precedence: stage s+1 must start after stage s completes
    def precedence_rule(m, t, s):
        if s < num_stages - 1:
            return m.start[t, s] + proc_time[t][s] <= m.start[t, s + 1]
        return pyo.Constraint.Skip

    model.precedence_con = pyo.Constraint(model.TASKS, model.STAGES, rule=precedence_rule)

    # Disjunctive constraints: no two operations on the same robot overlap
    # Build list of operations
    ops = [(t, s) for t in range(num_tasks) for s in range(num_stages)]
    num_ops = len(ops)

    model.PAIRS = pyo.Set(
        initialize=[(i, j) for i in range(num_ops) for j in range(i + 1, num_ops)]
    )

    model.seq = pyo.Var(model.PAIRS, within=pyo.Binary)

    def disjunctive_rule(m, i, j):
        t1, s1 = ops[i]
        t2, s2 = ops[j]
        if robot_assignment[t1][s1] != robot_assignment[t2][s2]:
            return pyo.Constraint.Skip
        return (
            m.start[t1, s1] + proc_time[t1][s1] <= m.start[t2, s2]
            + big_M * (1 - m.seq[i, j])
        )

    model.disjunctive_con = pyo.Constraint(model.PAIRS, rule=disjunctive_rule)

    def disjunctive_rule2(m, i, j):
        t1, s1 = ops[i]
        t2, s2 = ops[j]
        if robot_assignment[t1][s1] != robot_assignment[t2][s2]:
            return pyo.Constraint.Skip
        return (
            m.start[t2, s2] + proc_time[t2][s2] <= m.start[t1, s1]
            + big_M * m.seq[i, j]
        )

    model.disjunctive_con2 = pyo.Constraint(model.PAIRS, rule=disjunctive_rule2)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}