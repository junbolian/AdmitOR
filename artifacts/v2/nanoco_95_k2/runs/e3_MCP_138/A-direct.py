import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    conflict_edges = params["conflict_edges"]

    n_flights = 8
    flights = list(range(n_flights))
    horizon = sum(durations)

    model = pyo.ConcreteModel()

    model.start = pyo.Var(flights, within=pyo.NonNegativeReals)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    def makespan_rule(m, f):
        return m.start[f] + durations[f] <= m.makespan

    model.makespan_cons = pyo.Constraint(flights, rule=makespan_rule)
    model.makespan_bound = pyo.Constraint(expr=model.makespan <= horizon)

    model.conflict = pyo.ConstraintList()
    for (a, b) in conflict_edges:
        y = pyo.Var(within=pyo.Binary)
        model.add_component(f"prec_{a}_{b}", y)
        model.conflict.add(
            model.start[a] + durations[a] <= model.start[b] + horizon * (1 - y)
        )
        model.conflict.add(
            model.start[b] + durations[b] <= model.start[a] + horizon * y
        )

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}