import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    conflict_edges = params["conflict_edges"]

    flights = list(range(len(durations)))
    horizon = sum(durations[fm] for fm in flights)

    model = pyo.ConcreteModel()

    model.FLIGHTS = pyo.Set(initialize=flights)
    model.PAIRS = pyo.Set(initialize=list(conflict_edges), dimen=2)

    model.start = pyo.Var(model.FLIGHTS, domain=pyo.NonNegativeReals, bounds=(0, horizon))
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, horizon))

    # Big-M per pair
    model.y = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def finish_bound_rule(model, fm):
        return model.start[fm] + durations[fm] <= model.makespan
    model.finish_bound = pyo.Constraint(model.FLIGHTS, rule=finish_bound_rule)

    def nonoverlap_rule_a(model, fm, gn):
        M = horizon
        return model.start[fm] + durations[fm] <= model.start[gn] + M * (1 - model.y[(fm, gn)])
    model.nonoverlap_a = pyo.Constraint(model.PAIRS, rule=nonoverlap_rule_a)

    def nonoverlap_rule_b(model, fm, gn):
        M = horizon
        return model.start[gn] + durations[gn] <= model.start[fm] + M * model.y[(fm, gn)]
    model.nonoverlap_b = pyo.Constraint(model.PAIRS, rule=nonoverlap_rule_b)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}