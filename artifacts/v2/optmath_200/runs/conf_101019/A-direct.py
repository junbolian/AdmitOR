import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    cities = list(range(num_cities))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.cities = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    u_keys = [i for i in cities if i != 0]
    model.u = pyo.Var(u_keys, domain=pyo.NonNegativeReals)
    model.u0 = pyo.Var(initialize=float(params["u0_fixed"]))
    model.u0.fix(float(params["u0_fixed"]))

    def obj_rule(m):
        return sum(float(params["distance_%d_%d" % (i, j)]) * m.x[i, j] for (i, j) in m.arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_con = pyo.Constraint(model.cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_con = pyo.Constraint(model.cities, rule=in_rule)

    lb = float(params["u_lower_bound"])
    ub = float(params["u_upper_bound"])

    def ub_rule(m, i):
        return m.u[i] <= ub
    model.ub_con = pyo.Constraint(u_keys, rule=ub_rule)

    def lb_rule(m, i):
        return m.u[i] >= lb
    model.lb_con = pyo.Constraint(u_keys, rule=lb_rule)

    mtz_arcs = [(i, j) for (i, j) in arcs if i != 0 and j != 0]

    def mtz_rule(m, i, j):
        return m.u[i] - m.u[j] + num_cities * m.x[i, j] <= num_cities - 1
    model.mtz_con = pyo.Constraint(mtz_arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}