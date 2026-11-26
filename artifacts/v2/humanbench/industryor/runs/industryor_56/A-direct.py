import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    parts = list(range(1, 11))
    equipments = ["A", "B", "C"]

    cost_per_unit = {
        "A": {p: params["processing_cost_A"][p - 1] for p in parts},
        "B": {p: params["processing_cost_B"][p - 1] for p in parts},
        "C": {p: params["processing_cost_C"][p - 1] for p in parts},
    }

    model = pyo.ConcreteModel()

    model.parts = pyo.Set(initialize=parts)
    model.equip = pyo.Set(initialize=equipments)

    model.x = pyo.Var(model.parts, model.equip, domain=pyo.Binary)
    model.y = pyo.Var(model.equip, domain=pyo.Binary)

    def obj_rule(m):
        processing = sum(
            cost_per_unit[e][p] * m.x[p, e] for p in m.parts for e in m.equip
        )
        setup = (
            params["setup_cost_A"] * m.y["A"]
            + params["setup_cost_B"] * m.y["B"]
            + params["setup_cost_C"] * m.y["C"]
        )
        return processing + setup

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # (1) Each part processed exactly once
    def once_rule(m, p):
        return sum(m.x[p, e] for e in m.equip) == 1

    model.once = pyo.Constraint(model.parts, rule=once_rule)

    # setup linking
    def link_rule(m, p, e):
        return m.x[p, e] <= m.y[e]

    model.link = pyo.Constraint(model.parts, model.equip, rule=link_rule)

    # (2) If part 1 on A -> part 2 on B or C; if part 1 on B or C -> part 2 on A
    model.cond2a = pyo.Constraint(
        expr=model.x[2, "B"] + model.x[2, "C"] >= model.x[1, "A"]
    )
    model.cond2b = pyo.Constraint(
        expr=model.x[2, "A"] >= model.x[1, "B"] + model.x[1, "C"]
    )

    # (3) parts 3,4,5 on A,B,C respectively
    model.fix3 = pyo.Constraint(expr=model.x[3, "A"] == 1)
    model.fix4 = pyo.Constraint(expr=model.x[4, "B"] == 1)
    model.fix5 = pyo.Constraint(expr=model.x[5, "C"] == 1)

    # (4) number of parts on C <= max_parts_on_C
    model.maxC = pyo.Constraint(
        expr=sum(model.x[p, "C"] for p in model.parts)
        <= params["max_parts_on_C"]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}