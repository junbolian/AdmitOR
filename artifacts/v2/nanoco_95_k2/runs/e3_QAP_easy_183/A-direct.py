import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 4
    depts = list(range(n))
    zones = list(range(n))

    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    flow = {}
    dist = {}
    for (i, j) in pairs:
        key = "%d%d" % (i, j)
        flow[(i, j)] = params["flow_" + key]
        dist[(i, j)] = params["dist_" + key]

    coords = {}
    for z in zones:
        coords[z] = (params["coord_x%d" % z], params["coord_y%d" % z])

    model = pyo.ConcreteModel()

    model.D = pyo.Set(initialize=depts)
    model.Z = pyo.Set(initialize=zones)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.D, model.Z, domain=pyo.Binary)

    # auxiliary variable to keep objective degree manageable for HiGHS
    model.y = pyo.Var(model.P, model.Z, model.Z, domain=pyo.Binary)

    def dept_rule(m, d):
        return sum(m.x[d, z] for z in m.Z) == 1

    model.dept_con = pyo.Constraint(model.D, rule=dept_rule)

    def zone_rule(m, z):
        return sum(m.x[d, z] for d in m.D) == 1

    model.zone_con = pyo.Constraint(model.Z, rule=zone_rule)

    # Linearize y[i,j,a,b] = x[i,a]*x[j,b] for a != b
    def y_lb1(m, i, j, a, b):
        return m.y[i, j, a, b] >= m.x[i, a] + m.x[j, b] - 1

    def y_lb2(m, i, j, a, b):
        return m.y[i, j, a, b] >= 0

    def y_ub1(m, i, j, a, b):
        return m.y[i, j, a, b] <= m.x[i, a]

    def y_ub2(m, i, j, a, b):
        return m.y[i, j, a, b] <= m.x[j, b]

    def pair_zone_filter(m, i, j, a, b):
        return a != b

    model.y_con1 = pyo.Constraint(model.P, model.Z, model.Z, rule=y_lb1)
    model.y_con2 = pyo.Constraint(model.P, model.Z, model.Z, rule=y_ub1)
    model.y_con3 = pyo.Constraint(model.P, model.Z, model.Z, rule=y_ub2)

    def obj_rule(m):
        total = 0
        for (i, j) in pairs:
            f = flow[(i, j)]
            d_ij = dist[(i, j)]
            for a in zones:
                for b in zones:
                    if a != b:
                        total += f * d_ij * m.y[i, j, a, b]
        return total

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}