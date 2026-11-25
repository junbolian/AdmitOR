import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 4
    depts = list(range(n))
    zones = list(range(n))

    flow_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    flow = {}
    flow[(0, 1)] = params["flow_01"]
    flow[(0, 2)] = params["flow_02"]
    flow[(0, 3)] = params["flow_03"]
    flow[(1, 2)] = params["flow_12"]
    flow[(1, 3)] = params["flow_13"]
    flow[(2, 3)] = params["flow_23"]

    dist = {}
    dist[(0, 1)] = params["dist_01"]
    dist[(0, 2)] = params["dist_02"]
    dist[(0, 3)] = params["dist_03"]
    dist[(1, 2)] = params["dist_12"]
    dist[(1, 3)] = params["dist_13"]
    dist[(2, 3)] = params["dist_23"]

    def sym_flow(d1, d2):
        return flow[(d1, d2)] if (d1, d2) in flow else flow[(d2, d1)]

    def sym_dist(z1, z2):
        return dist[(z1, z2)] if (z1, z2) in dist else dist[(z2, z1)]

    model = pyo.ConcreteModel()

    model.D = pyo.Set(initialize=depts)
    model.Z = pyo.Set(initialize=zones)

    model.x = pyo.Var(model.D, model.Z, domain=pyo.Binary)

    # Each department assigned to exactly one zone
    def dept_rule(mdl, d):
        return sum(mdl.x[d, z] for z in mdl.Z) == 1

    model.dept_con = pyo.Constraint(model.D, rule=dept_rule)

    # Each zone accommodates exactly one department
    def zone_rule(mdl, z):
        return sum(mdl.x[d, z] for d in mdl.D) == 1

    model.zone_con = pyo.Constraint(model.Z, rule=zone_rule)

    # Linearized objective: y[d1,d2,z1,z2] = x[d1,z1] * x[d2,z2]
    model.pairs = pyo.Set(initialize=flow_pairs, dimen=2)
    model.y = pyo.Var(model.pairs, model.Z, model.Z, domain=pyo.Binary)

    def lin1_rule(mdl, d1, d2, z1, z2):
        return mdl.y[d1, d2, z1, z2] <= mdl.x[d1, z1]

    def lin2_rule(mdl, d1, d2, z1, z2):
        return mdl.y[d1, d2, z1, z2] <= mdl.x[d2, z2]

    def lin3_rule(mdl, d1, d2, z1, z2):
        return mdl.y[d1, d2, z1, z2] >= mdl.x[d1, z1] + mdl.x[d2, z2] - 1

    model.lin_con1 = pyo.Constraint(model.pairs, model.Z, model.Z, rule=lin1_rule)
    model.lin_con2 = pyo.Constraint(model.pairs, model.Z, model.Z, rule=lin2_rule)
    model.lin_con3 = pyo.Constraint(model.pairs, model.Z, model.Z, rule=lin3_rule)

    # Objective: minimize sum over department pairs of flow * distance between assigned zones
    def obj_rule(mdl):
        total = 0
        for (d1, d2) in flow_pairs:
            fval = sym_flow(d1, d2)
            for z1 in mdl.Z:
                for z2 in mdl.Z:
                    if z1 != z2:
                        total += fval * sym_dist(z1, z2) * mdl.y[d1, d2, z1, z2]
        return total

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}