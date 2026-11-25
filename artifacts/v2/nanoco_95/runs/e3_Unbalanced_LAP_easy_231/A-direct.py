import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = len(cost)
    m = len(cost[0])

    model = pyo.ConcreteModel()

    model.staff = pyo.RangeSet(0, n - 1)
    model.zones = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.staff, model.zones, domain=pyo.Binary)

    def obj_rule(model):
        return sum(cost[i][j] * model.x[i, j] for i in model.staff for j in model.zones)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def staff_rule(model, i):
        return sum(model.x[i, j] for j in model.zones) == 1

    model.staff_constraint = pyo.Constraint(model.staff, rule=staff_rule)

    def zone_rule(model, j):
        return sum(model.x[i, j] for i in model.staff) <= 1

    model.zone_constraint = pyo.Constraint(model.zones, rule=zone_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}