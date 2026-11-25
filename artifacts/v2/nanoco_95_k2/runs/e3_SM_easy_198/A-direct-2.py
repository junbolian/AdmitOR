import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    inv_rank = params["investor_rankings"]
    fnd_rank = params["founder_rankings"]

    n_inv = len(inv_rank)
    n_fnd = len(fnd_rank)

    investors = list(range(n_inv))
    founders = list(range(n_fnd))

    inv_pos = {i: {f: pos for pos, f in enumerate(inv_rank[i])} for i in investors}
    fnd_pos = {f: {i: pos for pos, i in enumerate(fnd_rank[f])} for f in founders}

    model = pyo.ConcreteModel()

    model.INV = pyo.Set(initialize=investors)
    model.FND = pyo.Set(initialize=founders)

    model.x = pyo.Var(model.INV, model.FND, domain=pyo.Binary)

    def inv_rule(m, i):
        return sum(m.x[i, f] for f in m.FND) == 1
    model.inv_con = pyo.Constraint(model.INV, rule=inv_rule)

    def fnd_rule(m, f):
        return sum(m.x[i, f] for i in m.INV) == 1
    model.fnd_con = pyo.Constraint(model.FND, rule=fnd_rule)

    # Stability: (i,f) cannot be a blocking pair.
    # If i is matched with someone worse than f, then f must not be with someone
    # worse than i (else they'd block). Formulation:
    #   sum_{f' worse than f for i} x[i,f'] + sum_{i' worse than i for f} x[i',f] <= 1
    def stab_rule(m, i, f):
        worse_f = [f2 for f2 in founders if inv_pos[i][f2] > inv_pos[i][f]]
        worse_i = [i2 for i2 in investors if fnd_pos[f][i2] > fnd_pos[f][i]]
        if not worse_f and not worse_i:
            return pyo.Constraint.Feasible
        expr = sum(m.x[i, f2] for f2 in worse_f) + sum(m.x[i2, f] for i2 in worse_i)
        return expr <= 1
    model.stab_con = pyo.Constraint(model.INV, model.FND, rule=stab_rule)

    def obj_rule(m):
        return sum(
            (inv_pos[i][f] + fnd_pos[f][i]) * m.x[i, f]
            for i in m.INV for f in m.FND
        )
    model.total_misfit = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_misfit))
    return {"objective": obj_val, "status": "optimal"}