# IR: {"sets":{"I":[0,1,2,3,4,5],"H":[0,1,2,3,4,5]},"params":{"supply_weights":"weight[i] for i in I","hospital_capacity":"uniform capacity"},"variables":{"x[i,h]":"binary supply assignment","y[h]":"binary hospital use"},"constraints":["sum(h in H) x[i,h] = 1 for each i in I","sum(i in I) supply_weights[i]*x[i,h] <= hospital_capacity*y[h] for each h in H","x[i,h] <= y[h] for each i in I, h in H"],"objective":"minimize sum(h in H) y[h]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_weights = params["supply_weights"]
    hospital_capacity = params["hospital_capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.H = pyo.RangeSet(0, 5)

    model.weight = pyo.Param(
        model.I,
        initialize={i: supply_weights[i] for i in model.I},
    )
    model.capacity = pyo.Param(initialize=hospital_capacity)

    model.x = pyo.Var(model.I, model.H, domain=pyo.Binary)
    model.y = pyo.Var(model.H, domain=pyo.Binary)

    def assignment_rule(block, i):
        return sum(block.x[i, h] for h in block.H) == 1

    model.assignment_constraints = pyo.Constraint(
        model.I, rule=assignment_rule
    )

    def capacity_rule(block, h):
        return (
            sum(block.weight[i] * block.x[i, h] for i in block.I)
            <= block.capacity * block.y[h]
        )

    model.capacity_constraints = pyo.Constraint(
        model.H, rule=capacity_rule
    )

    def usage_rule(block, i, h):
        return block.x[i, h] <= block.y[h]

    model.usage_constraints = pyo.Constraint(
        model.I, model.H, rule=usage_rule
    )

    model.total_hospitals = pyo.Objective(
        expr=sum(model.y[h] for h in model.H),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_hospitals))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}