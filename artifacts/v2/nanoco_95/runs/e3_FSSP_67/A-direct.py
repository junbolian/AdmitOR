import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_times"]
    n_st = int(params["num_stations"])
    n_b = int(params["num_batches"])

    stations = list(range(n_st))
    batches = list(range(n_b))

    def p(b, s):
        return pt[b * n_st + s]

    # Upper bound on makespan for big-M
    bigM = sum(pt)

    model = pyo.ConcreteModel()
    model.S = pyo.Set(initialize=stations)
    model.B = pyo.Set(initialize=batches)

    # Start and completion times
    model.x = pyo.Var(model.B, model.S, within=pyo.NonNegativeReals)
    model.C = pyo.Var(model.B, within=pyo.NonNegativeReals)

    # Makespan
    model.T = pyo.Var(within=pyo.NonNegativeReals)

    # Precedence within each batch (flow shop)
    def prec_rule(mdl, b, s):
        if s == 0:
            return pyo.Constraint.Skip
        return mdl.x[b, s] >= mdl.x[b, s - 1] + p(b, s - 1)

    model.prec = pyo.Constraint(model.B, model.S, rule=prec_rule)

    # Completion time of last station for each batch
    def comp_rule(mdl, b):
        return mdl.C[b] == mdl.x[b, n_st - 1] + p(b, n_st - 1)

    model.comp = pyo.Constraint(model.B, rule=comp_rule)

    # Makespan definition
    model.makespan = pyo.Constraint(
        model.B, rule=lambda mdl, b: mdl.T >= mdl.C[b]
    )

    # Disjunctive constraints: for each station, order every pair of batches
    pairs = [(b1, b2) for b1 in batches for b2 in batches if b1 < b2]

    model.P = pyo.Set(initialize=pairs, dimen=2)
    # y[b1,b2,s] = 1 if batch b1 precedes b2 on station s
    model.y = pyo.Var(model.P, model.S, within=pyo.Binary)

    def disj1_rule(mdl, b1, b2, s):
        return mdl.x[b2, s] >= mdl.x[b1, s] + p(b1, s) - bigM * (1 - mdl.y[b1, b2, s])

    def disj2_rule(mdl, b1, b2, s):
        return mdl.x[b1, s] >= mdl.x[b2, s] + p(b2, s) - bigM * mdl.y[b1, b2, s]

    model.disj1 = pyo.Constraint(model.P, model.S, rule=disj1_rule)
    model.disj2 = pyo.Constraint(model.P, model.S, rule=disj2_rule)

    model.obj = pyo.Objective(expr=model.T, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}