import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)

    model = pyo.ConcreteModel()
    model.staff = pyo.RangeSet(0, n - 1)
    model.zones = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.staff, model.zones, domain=pyo.Binary)

    model.staff_assign = pyo.Constraint(
        model.staff,
        rule=lambda mm, i: sum(mm.x[i, j] for j in mm.zones) == 1,
    )
    model.zone_assign = pyo.Constraint(
        model.zones,
        rule=lambda mm, j: sum(mm.x[i, j] for i in mm.staff) == 1,
    )

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j]
                 for i in model.staff for j in model.zones),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}