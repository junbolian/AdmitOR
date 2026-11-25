import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    int_ = params["participant_interest"]
    cap_part = params["max_assignments_per_participant"]
    cap_car = params["max_assignments_per_car"]

    participants = range(len(int_))
    cars = range(len(int_[0])) if len(int_) > 0 else range(0)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(participants))
    model.C = pyo.Set(initialize=list(cars))

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    eligible = [(p, c) for p in participants for c in cars if int_[p][c] == 1]
    model.eligible = pyo.Set(initialize=eligible, dimen=2)

    # Disallow ineligible assignments
    model.no_ineligible = pyo.Constraint(
        model.P, model.C,
        rule=lambda mdl, p, c: mdl.x[p, c] == 0 if (p, c) not in eligible else pyo.Constraint.Skip
    )

    def part_rule(mdl, p):
        return sum(mdl.x[p, c] for c in mdl.C) <= cap_part
    
    def car_rule(mdl, c):
        return sum(mdl.x[p, c] for p in mdl.P) <= cap_car

    model.part_cap = pyo.Constraint(model.P, rule=part_rule)
    model.car_cap = pyo.Constraint(model.C, rule=car_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in eligible),
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}