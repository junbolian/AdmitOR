import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = [0, 1, 2]
    arcs = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]

    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.pos = pyo.Var(cities, domain=pyo.Reals)
    model.pos[1].setlb(params["pos1_lower"])
    model.pos[1].setub(params["pos1_upper"])
    model.pos[2].setlb(params["pos2_lower"])
    model.pos[2].setub(params["pos2_upper"])

    def obj_rule(m):
        return sum(cost[a] * m.x[a] for a in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.visit_0 = pyo.Constraint(expr=model.x[1, 0] + model.x[2, 0] == 1)
    model.visit_1 = pyo.Constraint(expr=model.x[0, 1] + model.x[2, 1] == 1)
    model.visit_2 = pyo.Constraint(expr=model.x[0, 2] + model.x[1, 2] == 1)

    model.depart_0 = pyo.Constraint(expr=model.x[0, 1] + model.x[0, 2] == 1)
    model.depart_1 = pyo.Constraint(expr=model.x[1, 0] + model.x[1, 2] == 1)
    model.depart_2 = pyo.Constraint(expr=model.x[2, 0] + model.x[2, 1] == 1)

    model.sec_1_2 = pyo.Constraint(
        expr=model.pos[1] - model.pos[2] <= -1 + 3 * (1 - model.x[1, 2])
    )
    model.sec_2_1 = pyo.Constraint(
        expr=model.pos[2] - model.pos[1] <= -1 + 3 * (1 - model.x[2, 1])
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}