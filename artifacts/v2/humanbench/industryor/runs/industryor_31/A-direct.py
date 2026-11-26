import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    car_lengths = params["car_lengths"]
    side_capacity = params["side_capacity"]
    n = len(car_lengths)

    model = pyo.ConcreteModel()
    model.cars = pyo.RangeSet(0, n - 1)
    model.sides = pyo.RangeSet(0, 1)

    # x[i, s] = 1 if car i is parked on side s
    model.x = pyo.Var(model.cars, model.sides, domain=pyo.Binary)

    # y[s] = total length used on side s
    model.y = pyo.Var(model.sides, domain=pyo.NonNegativeReals, bounds=(0, side_capacity))

    # z = total street length occupied = max(y[0], y[1])
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    # each car assigned to exactly one side
    def assign_rule(mdl, i):
        return sum(mdl.x[i, s] for s in mdl.sides) == 1

    model.assign = pyo.Constraint(model.cars, rule=assign_rule)

    # side length definitions and capacity
    def side_rule(mdl, s):
        return mdl.y[s] == sum(car_lengths[i] * mdl.x[i, s] for i in mdl.cars)

    model.side = pyo.Constraint(model.sides, rule=side_rule)

    # z >= each side length (minimizing z gives max)
    def z_rule(mdl, s):
        return mdl.z >= mdl.y[s]

    model.zcon = pyo.Constraint(model.sides, rule=z_rule)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_unbounded"}

    return {"objective": obj_val, "status": "optimal"}