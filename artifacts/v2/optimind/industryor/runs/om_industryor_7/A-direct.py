import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    workers = ["I", "II", "III", "IV", "V"]
    tasks = ["A", "B", "C", "D"]

    time_data = {}
    for w in workers:
        for t in tasks:
            time_data[(w, t)] = params["time_{}_{}".format(w, t)]

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=workers)
    model.T = pyo.Set(initialize=tasks)

    model.x = pyo.Var(model.W, model.T, domain=pyo.Binary)

    def obj_rule(m):
        return sum(time_data[(w, t)] * m.x[w, t] for w in m.W for t in m.T)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each task assigned exactly one worker
    def task_rule(m, t):
        return sum(m.x[w, t] for w in m.W) == 1

    model.task_con = pyo.Constraint(model.T, rule=task_rule)

    # Each worker assigned at most one task
    def worker_rule(m, w):
        return sum(m.x[w, t] for t in m.T) <= 1

    model.worker_con = pyo.Constraint(model.W, rule=worker_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}