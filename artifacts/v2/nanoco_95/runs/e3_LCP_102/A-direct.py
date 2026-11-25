import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_zones = int(params["num_warehouse_zones"])

    allowed = {}
    for z in range(num_zones):
        allowed[z] = [int(t) for t in params["zone_%d_allowed_types" % z]]

    pairs = []
    for p in params["incompatibility_pairs"]:
        pairs.append((int(p[0]), int(p[1])))

    all_types = sorted({t for z in range(num_zones) for t in allowed[z]})

    model = pyo.ConcreteModel()
    model.Z = pyo.Set(initialize=list(range(num_zones)), ordered=True)
    model.T = pyo.Set(initialize=all_types, ordered=True)
    model.K = pyo.Set(initialize=list(range(len(pairs))), ordered=True)

    model.x = pyo.Var(model.Z, model.T, domain=pyo.Binary)
    model.M = pyo.Var(domain=pyo.NonNegativeReals)

    def assign_rule(m, z):
        return sum(m.x[z, t] for t in allowed[z]) == 1

    model.assign = pyo.Constraint(model.Z, rule=assign_rule)

    def forbid_rule(m, z, t):
        if t in allowed[z]:
            return pyo.Constraint.Skip
        return m.x[z, t] == 0

    model.forbid = pyo.Constraint(model.Z, model.T, rule=forbid_rule)

    def incompat_rule(m, k):
        a, b = pairs[k]
        return sum(m.x[a, t] + m.x[b, t] for t in all_types) <= 1

    model.incompat = pyo.Constraint(model.K, rule=incompat_rule)

    def max_rule(m, z, t):
        if t in allowed[z]:
            return m.M >= t * m.x[z, t]
        return pyo.Constraint.Skip

    model.maxlink = pyo.Constraint(model.Z, model.T, rule=max_rule)

    model.obj = pyo.Objective(expr=model.M, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}