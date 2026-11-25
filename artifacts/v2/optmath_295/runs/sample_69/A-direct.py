import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }

    lb = params["u_bound_lower"]
    ub = params["u_bound_upper"]
    u0 = params["u_city0"]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.cities = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    u_index = [0, 1, 2, 3]
    model.u = pyo.Var(u_index, domain=pyo.Reals)

    # Fix u[0] and bound the others
    def u_lb_rule(mdl, i):
        return mdl.u[i] >= (u0 if i == 0 else lb)

    def u_ub_rule(mdl, i):
        return mdl.u[i] <= (u0 if i == 0 else ub)

    model.u_lb_cons = pyo.Constraint(u_index, rule=u_lb_rule)
    model.u_ub_cons = pyo.Constraint(u_index, rule=u_ub_rule)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1

    model.out_cons = pyo.Constraint(model.cities, rule=out_rule)
    model.in_cons = pyo.Constraint(model.cities, rule=in_rule)

    big_m = ub + 1

    def mt_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + big_m * mdl.x[(i, j)] <= big_m - 1

    model.mt_cons = pyo.Constraint(model.arcs, rule=mt_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}