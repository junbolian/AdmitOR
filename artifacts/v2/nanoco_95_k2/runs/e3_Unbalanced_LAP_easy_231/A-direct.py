import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost_matrix = params["cost_matrix"]
    num_staff = len(cost_matrix)
    num_zones = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.staff = pyo.RangeSet(0, num_staff - 1)
    model.zones = pyo.RangeSet(0, num_zones - 1)

    model.cost = pyo.Param(model.staff, model.zones,
                           initialize=lambda m, i, j: cost_matrix[i][j])

    model.assign = pyo.Var(model.staff, model.zones, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.cost[i, j] * model.assign[i, j]
                 for i in model.staff for j in model.zones),
        sense=pyo.minimize
    )

    model.staff_constraint = pyo.Constraint(
        model.staff,
        rule=lambda m, i: sum(m.assign[i, j] for j in m.zones) == 1
    )

    model.zone_constraint = pyo.Constraint(
        model.zones,
        rule=lambda m, j: sum(m.assign[i, j] for i in m.staff) <= 1
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}