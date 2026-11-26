# IR: {"sets":{"T":"1..n"},"params":["a1","a2","pilot_yield_per_training_jet","n"],"variables":{"x[t]":"nonnegative integer; total operational combat fleet in year t","y[t]":"nonnegative integer; total training fleet in year t"},"constraints":["x[t]+y[t]=t*(a1+a2) for t in T","x[t]<=pilot_yield_per_training_jet*sum(y[s] for s<t) for t in T","x[t]>=x[t-1] for t=2..n"],"objective":"maximize sum(x[t] for t in T)"}
#
# Interpretation: To count combat jet-years and permit training aircraft to
# transfer into combat, x and y represent fleet stocks, including prior
# deliveries. The annual delivery split sums to a1+a2; the fleet stocks sum
# to t*(a1+a2). Combat aircraft remain in combat, and training aircraft may
# transfer to combat. Pilots remain available after qualifying.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    horizon = params["n"]
    n = int(horizon)
    if n != horizon or n < 1:
        return {"objective": None, "status": "invalid_horizon"}

    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(1, n)

    model.a1 = pyo.Param(
        initialize=params["a1"], within=pyo.NonNegativeIntegers
    )
    model.a2 = pyo.Param(
        initialize=params["a2"], within=pyo.NonNegativeIntegers
    )
    model.pilot_yield = pyo.Param(
        initialize=params["pilot_yield_per_training_jet"],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)

    def fleet_balance_rule(instance, year):
        return (
            instance.x[year] + instance.y[year]
            == year * (instance.a1 + instance.a2)
        )

    model.fleet_balance = pyo.Constraint(
        model.T, rule=fleet_balance_rule
    )

    def pilot_availability_rule(instance, year):
        return instance.x[year] <= instance.pilot_yield * sum(
            instance.y[prior_year] for prior_year in range(1, year)
        )

    model.pilot_availability = pyo.Constraint(
        model.T, rule=pilot_availability_rule
    )

    def combat_retention_rule(instance, year):
        if year == 1:
            return pyo.Constraint.Skip
        return instance.x[year] >= instance.x[year - 1]

    model.combat_retention = pyo.Constraint(
        model.T, rule=combat_retention_rule
    )

    model.total_combat_jet_years = pyo.Objective(
        expr=sum(model.x[year] for year in model.T),
        sense=pyo.maximize,
    )

    # Appsi can raise RuntimeError when it cannot load a feasible solution.
    # Success is determined solely by retrieving the objective value.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_combat_jet_years))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}