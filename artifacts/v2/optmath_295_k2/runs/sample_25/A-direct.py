import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3]
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
    arcs = list(cost.keys())

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i, j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i and (i, j) in cost) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j and (i, j) in cost) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    model.pos0 = pyo.Constraint(expr=model.u[0] == params["position_city_0"])

    def pos_bounds_rule(mdl, i):
        return (params["position_lower_bound"], mdl.u[i], params["position_upper_bound"])

    model.pos_bounds = pyo.Constraint([1, 2, 3], rule=pos_bounds_rule)

    BigM = params["mtz_big_M"]
    rhs = params["mtz_rhs"]

    def mtz_rule(mdl, i, j):
        return BigM * mdl.x[i, j] + mdl.u[i] - mdl.u[j] <= rhs

    mtz_set = [(i, j) for (i, j) in arcs if i != 0 and j != 0]
    model.mtz = pyo.Constraint(mtz_set, rule=mtz_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution"}

    return {"objective": obj_val, "status": "optimal"}