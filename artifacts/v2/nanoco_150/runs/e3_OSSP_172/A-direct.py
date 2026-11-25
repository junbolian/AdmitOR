import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    prototypes = ["P0", "P1", "P2"]
    stations = ["S0", "S1", "S2"]

    dur = {}
    for p in prototypes:
        for s in stations:
            dur[(p, s)] = params[f"duration_{p}_{s}"]

    tasks = [(p, s) for p in prototypes for s in stations]
    n = len(tasks)
    BIG = sum(dur.values())

    model = pyo.ConcreteModel()
    model.TASK = pyo.Set(initialize=range(n), ordered=True)

    model.start = pyo.Var(model.TASK, domain=pyo.NonNegativeReals, bounds=(0, BIG))
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, BIG))

    # assign each task index to (prototype, station)
    task_proto = [t[0] for t in tasks]
    task_station = [t[1] for t in tasks]
    task_dur = [dur[t] for t in tasks]

    # makespan
    def cmax_rule(m, i):
        return m.Cmax >= m.start[i] + task_dur[i]

    model.cmax_con = pyo.Constraint(model.TASK, rule=cmax_rule)

    # disjunctive constraints for every pair of tasks that share a resource
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            same_station = task_station[i] == task_station[j]
            same_proto = task_proto[i] == task_proto[j]
            if same_station or same_proto:
                pairs.append((i, j))

    model.PAIR = pyo.Set(initialize=range(len(pairs)), ordered=True)
    model.y = pyo.Var(model.PAIR, domain=pyo.Binary)

    def ordering_rule(m, k):
        i, j = pairs[k]
        di = task_dur[i]
        dj = task_dur[j]
        # y=1 -> i before j ; y=0 -> j before i
        return m.start[i] + di <= m.start[j] + BIG * (1 - m.y[k])

    def ordering_rule2(m, k):
        i, j = pairs[k]
        di = task_dur[i]
        dj = task_dur[j]
        return m.start[j] + dj <= m.start[i] + BIG * m.y[k]

    model.order1 = pyo.Constraint(model.PAIR, rule=ordering_rule)
    model.order2 = pyo.Constraint(model.PAIR, rule=ordering_rule2)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}