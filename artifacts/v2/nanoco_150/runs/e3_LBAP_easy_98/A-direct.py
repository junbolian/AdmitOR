import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    ptime = params["processing_time"]

    n_machines = len(ptime)
    n_jobs = len(ptime[0])

    model = pyo.ConcreteModel()
    model.M = pyo.RangeSet(0, n_machines - 1)
    model.J = pyo.RangeSet(0, n_jobs - 1)

    model.x = pyo.Var(model.M, model.J, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    def assign_machine_rule(model, i):
        return sum(model.x[i, j] for j in model.J) == 1

    def assign_job_rule(model, j):
        return sum(model.x[i, j] for i in model.M) == 1

    def makespan_rule(model, i, j):
        return model.z >= ptime[i][j] * model.x[i, j]

    model.machine_constraint = pyo.Constraint(model.M, rule=assign_machine_rule)
    model.job_constraint = pyo.Constraint(model.J, rule=assign_job_rule)
    model.makespan_constraint = pyo.Constraint(model.M, model.J, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}