# IR: {"sets":{"I":"{0,1,2,3}","B":"{0,...,max(1,sum(demands))-1}"},"params":{"bolt_length":"positive number","strip_lengths":"four positive numbers indexed by I","demands":"four nonnegative integers indexed by I"},"variables":{"used[b]":"binary, b in B","cut[i,b]":"nonnegative integer, i in I, b in B"},"constraints":["For each i: sum_b cut[i,b] = demands[i].","For each b: sum_i strip_lengths[i]*cut[i,b] <= bolt_length*used[b]."],"objective":"Minimize sum_b used[b]."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bolt_length = params["bolt_length"]
    strip_lengths = list(params["strip_lengths"])
    raw_demands = list(params["demands"])

    if len(strip_lengths) != 4 or len(raw_demands) != 4:
        return {"objective": None, "status": "invalid_parameters"}

    if not math.isfinite(bolt_length) or bolt_length <= 0:
        return {"objective": None, "status": "invalid_parameters"}

    if any(
        not math.isfinite(length) or length <= 0
        for length in strip_lengths
    ):
        return {"objective": None, "status": "invalid_parameters"}

    if any(
        not math.isfinite(quantity)
        or quantity < 0
        or quantity != int(quantity)
        for quantity in raw_demands
    ):
        return {"objective": None, "status": "invalid_parameters"}

    demands = [int(quantity) for quantity in raw_demands]

    # One candidate bolt per demanded piece suffices whenever feasible.
    # Retain one candidate for an empty order so the model remains solvable.
    candidate_count = max(1, sum(demands))

    model = pyo.ConcreteModel()
    model.strip_types = pyo.Set(initialize=range(4), ordered=True)
    model.bolts = pyo.Set(initialize=range(candidate_count), ordered=True)

    model.used = pyo.Var(model.bolts, domain=pyo.Binary)
    model.cut = pyo.Var(
        model.strip_types,
        model.bolts,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(mdl, strip_type):
        return (
            sum(mdl.cut[strip_type, bolt] for bolt in mdl.bolts)
            == demands[strip_type]
        )

    model.demand_balance = pyo.Constraint(
        model.strip_types, rule=demand_rule
    )

    def capacity_rule(mdl, bolt):
        return (
            sum(
                strip_lengths[strip_type] * mdl.cut[strip_type, bolt]
                for strip_type in mdl.strip_types
            )
            <= bolt_length * mdl.used[bolt]
        )

    model.bolt_capacity = pyo.Constraint(
        model.bolts, rule=capacity_rule
    )

    model.total_bolts = pyo.Objective(
        expr=sum(model.used[bolt] for bolt in model.bolts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_bolts))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}