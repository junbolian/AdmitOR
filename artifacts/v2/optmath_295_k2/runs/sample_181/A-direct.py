import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    def cost_of(i, j):
        return params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.Reals)

    def obj_rule(m):
        return sum(cost_of(i, j) * m.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_constraint = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_constraint = pyo.Constraint(cities, rule=in_rule)

    non_root = [1, 2, 3, 4]
    model.u_bound = pyo.Constraint(
        non_root, rule=lambda m, i: pyo.inequality(
            params["u_lower"], m.u[i], params["u_upper"]
        )
    )
    model.u_zero_fix = pyo.Constraint(expr=model.u[0] == 0)

    mt_arcs = [(i, j) for (i, j) in arcs if i != 0 and j != 0]

    def mt_rule(m, i, j):
        return m.u[j] >= m.u[i] + 1 - 5 * (1 - m.x[i, j])
    model.mtz = pyo.Constraint(mt_arcs, rule=mt_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}