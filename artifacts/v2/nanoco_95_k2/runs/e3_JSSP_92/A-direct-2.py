import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proc_time = params["proc_time"]
    robot_assignment = params["robot_assignment"]

    num_tasks = len(proc_time)
    num_stages = len(proc_time[0])

    model = pyo.ConcreteModel()

    model.TASKS = pyo.RangeSet(0, num_tasks - 1)
    model.STAGES = pyo.RangeSet(0, num_stages - 1)

    model.start = pyo.Var(model.TASKS, model.STAGES, domain=pyo.NonNegativeReals)
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    # Precedence within each task
    def precedence_rule(m, i, j):
        if j >= 1:
            return m.start[i, j] >= m.start[i, j - 1] + proc_time[i][j - 1]
        return pyo.Constraint.Skip

    model.precedence = pyo.Constraint(
        model.TASKS, model.STAGES, rule=precedence_rule
    )

    # Makespan lower bound from each task's last operation
    def makespan_rule(m, i):
        return m.makespan >= m.start[i, num_stages - 1] + proc_time[i][num_stages - 1]

    model.makespan_con = pyo.Constraint(model.TASKS, rule=makespan_rule)

    # Build list of operations per robot
    robots = sorted({robot_assignment[i][j] for i in range(num_tasks) for j in range(num_stages)})
    robot_ops = {r: [] for r in robots}
    for i in range(num_tasks):
        for j in range(num_stages):
            r = robot_assignment[i][j]
            robot_ops[r].append((i, j))

    # Disjunctive constraints: exactly one ordering per pair on same robot
    # using a binary variable to choose the ordering
    model.pairs = pyo.Set(initialize=[])
    pair_list = []
    for r in robots:
        ops = robot_ops[r]
        for a in range(len(ops)):
            for b in range(a + 1, len(ops)):
                pair_list.append((ops[a][0], ops[a][1], ops[b][0], ops[b][1]))

    model.PAIRS = pyo.Set(initialize=list(range(len(pair_list))), ordered=True)
    model.y = pyo.Var(model.PAIRS, domain=pyo.Binary)

    model.disj = pyo.ConstraintList()
    for k in model.PAIRS:
        i1, j1, i2, j2 = pair_list[k]
        p1 = proc_time[i1][j1]
        p2 = proc_time[i2][j2]
        # y=0: op1 before op2 ; y=1: op2 before op1
        bigM = sum(sum(row) for row in proc_time)
        model.disj.add(
            model.start[i1, j1] + p1 <= model.start[i2, j2] + bigM * model.y[k]
        )
        model.disj.add(
            model.start[i2, j2] + p2 <= model.start[i1, j1] + bigM * (1 - model.y[k])
        )

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}