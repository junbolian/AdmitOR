import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    tasks = [1, 2, 3, 4, 5, 6, 7]
    vms = [1, 2, 3]

    capacity = {
        1: params["capacity_VM1"],
        2: params["capacity_VM2"],
        3: params["capacity_VM3"],
    }
    usage = {
        1: dict(zip(tasks, params["usage_VM1"])),
        2: dict(zip(tasks, params["usage_VM2"])),
        3: dict(zip(tasks, params["usage_VM3"])),
    }
    cost = {
        1: dict(zip(tasks, params["cost_VM1"])),
        2: dict(zip(tasks, params["cost_VM2"])),
        3: dict(zip(tasks, params["cost_VM3"])),
    }

    model = pyo.ConcreteModel()

    model.tasks = pyo.Set(initialize=tasks)
    model.vms = pyo.Set(initialize=vms)

    model.x = pyo.Var(model.tasks, model.vms, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[v][t] * m.x[t, v] for t in m.tasks for v in m.vms)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, t):
        return sum(m.x[t, v] for v in m.vms) == 1

    model.assign_constraint = pyo.Constraint(model.tasks, rule=assign_rule)

    def cap_rule(m, v):
        return sum(usage[v][t] * m.x[t, v] for t in m.tasks) <= capacity[v]

    model.capacity_constraint = pyo.Constraint(model.vms, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}