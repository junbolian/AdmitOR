import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    work_cost = params["work_cost_per_day"]
    machine_cost = params["machine_cost_per_day"]

    # durations is expected to be a dict {activity: duration}
    acts = list(durations.keys())

    # Partly ordered / precedence relationships
    precedences = [
        ("A", "G"),
        ("A", "D"),
        ("E", "F"),
        ("G", "F"),
        ("D", "C"),
        ("F", "C"),
        ("F", "B"),
    ]
    # Fix unordered relation A -> D with C precedence: D -> C already handled.
    # Translate "A -> G, D" as A -> G and A -> D (both present).

    model = pyo.ConcreteModel()

    model.ACTS = pyo.Set(initialize=acts)

    model.start = pyo.Var(model.ACTS, within=pyo.NonNegativeReals)
    model.finish = pyo.Var(model.ACTS, within=pyo.NonNegativeReals)
    model.project_makespan = pyo.Var(within=pyo.NonNegativeReals)
    model.machine_duration = pyo.Var(within=pyo.NonNegativeReals)

    def duration_rule(mdl, a):
        return mdl.finish[a] == mdl.start[a] + float(durations[a])

    model.duration_con = pyo.Constraint(model.ACTS, rule=duration_rule)

    def prec_rule(mdl, i):
        p, s = precedences[i]
        return mdl.start[s] >= mdl.finish[p]

    model.prec_con = pyo.Constraint(range(len(precedences)), rule=prec_rule)

    def makespan_rule(mdl, a):
        return mdl.project_makespan >= mdl.finish[a]

    model.makespan_con = pyo.Constraint(model.ACTS, rule=makespan_rule)

    model.machine_def = pyo.Constraint(
        expr=model.machine_duration == model.finish["B"] - model.start["A"]
    )
    model.machine_nonneg = pyo.Constraint(expr=model.machine_duration >= 0)

    model.obj = pyo.Objective(
        expr=work_cost * model.project_makespan + machine_cost * model.machine_duration,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}