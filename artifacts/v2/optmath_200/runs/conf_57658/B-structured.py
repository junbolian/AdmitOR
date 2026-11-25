# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4]},"params":{"pref_p0_c0":"interest[0,0]","pref_p0_c1":"interest[0,1]","pref_p1_c4":"interest[1,4]","pref_p2_none":"frozen placeholder, read but not used","pref_p3_none":"frozen placeholder, read but not used","pref_p4_c0":"interest[4,0]","pref_p4_c2":"interest[4,2]","participant_capacity":"participant assignment limit","car_capacity":"car assignment limit","unlisted_interest":"structural zero"},"variables":{"x[p,c]":"binary for P x C"},"constraints":["x[p,c] <= interest[p,c] for all p,c","sum_c x[p,c] <= participant_capacity for all p","sum_p x[p,c] <= car_capacity for all c"],"objective":"maximize sum_{p,c} x[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    interests = {
        (0, 0): params["pref_p0_c0"],
        (0, 1): params["pref_p0_c1"],
        (1, 4): params["pref_p1_c4"],
        (4, 0): params["pref_p4_c0"],
        (4, 2): params["pref_p4_c2"],
    }
    frozen_placeholders = (
        params["pref_p2_none"],
        params["pref_p3_none"],
    )
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 4)
    model.C = pyo.RangeSet(0, 4)

    model.interest = pyo.Param(
        model.P, model.C, initialize=interests, default=0
    )
    model.participant_limit = pyo.Param(initialize=participant_capacity)
    model.car_limit = pyo.Param(initialize=car_capacity)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def interest_rule(block, participant, car):
        return block.x[participant, car] <= block.interest[participant, car]

    model.interest_constraints = pyo.Constraint(
        model.P, model.C, rule=interest_rule
    )

    def participant_rule(block, participant):
        return (
            sum(block.x[participant, car] for car in block.C)
            <= block.participant_limit
        )

    model.participant_constraints = pyo.Constraint(
        model.P, rule=participant_rule
    )

    def car_rule(block, car):
        return (
            sum(block.x[participant, car] for participant in block.P)
            <= block.car_limit
        )

    model.car_constraints = pyo.Constraint(model.C, rule=car_rule)

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.x[participant, car]
            for participant in model.P
            for car in model.C
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}