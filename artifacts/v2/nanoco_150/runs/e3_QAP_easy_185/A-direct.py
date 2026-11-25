import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 5

    flow = {}
    for i in range(n):
        for j in range(n):
            if i < j:
                flow[(i, j)] = params["flow_%d%d" % (i, j)]

    dist = {}
    for i in range(n):
        for j in range(n):
            if i < j:
                dist[(i, j)] = params["dist_%d%d" % (i, j)]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=list(range(n)))
    model.L = pyo.Set(initialize=list(range(n)))

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)

    model.assign_fac = pyo.Constraint(
        model.F, rule=lambda mdl, i: sum(mdl.x[i, l] for l in mdl.L) == 1
    )
    model.assign_loc = pyo.Constraint(
        model.L, rule=lambda mdl, l: sum(mdl.x[i, l] for i in mdl.F) == 1
    )

    # Linearized objective: y[i,j,k,l] = x[i,k] * x[j,l] for i<j, k<l, k!=l
    pair_ik = [(i, j, k, l) for (i, j) in flow for (k, l) in dist if k != l]
    model.P = pyo.Set(initialize=pair_ik, dimen=4)
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    def link1(mdl, i, j, k, l):
        return mdl.y[i, j, k, l] <= mdl.x[i, k]

    def link2(mdl, i, j, k, l):
        return mdl.y[i, j, k, l] <= mdl.x[j, l]

    def link3(mdl, i, j, k, l):
        return mdl.y[i, j, k, l] >= mdl.x[i, k] + mdl.x[j, l] - 1

    model.c1 = pyo.Constraint(model.P, rule=link1)
    model.c2 = pyo.Constraint(model.P, rule=link2)
    model.c3 = pyo.Constraint(model.P, rule=link3)

    def obj_rule(mdl):
        total = 0
        for (i, j) in flow:
            f = flow[(i, j)]
            for (k, l) in dist:
                if k != l:
                    d = dist[(k, l)]
                    total += f * d * mdl.y[i, j, min(k, l), max(k, l)] if False else 0
        return total

    # Build linear objective explicitly over ordered (k,l) with k<l, both orientations
    obj_terms = []
    for (i, j) in flow:
        f = flow[(i, j)]
        for (k, l) in dist:
            d = dist[(k, l)]
            # orientation x[i,k]*x[j,l] -> y indexed by (i,j,k,l)
            if (i, j, k, l) in pair_ik:
                obj_terms.append((f * d, (i, j, k, l)))
            # orientation x[i,l]*x[j,k] -> y indexed by (i,j,l,k)
            if (i, j, l, k) in pair_ik:
                obj_terms.append((f * d, (i, j, l, k)))

    def obj_rule2(mdl):
        return sum(coef * mdl.y[idx] for coef, idx in obj_terms)

    model.obj = pyo.Objective(rule=obj_rule2, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}