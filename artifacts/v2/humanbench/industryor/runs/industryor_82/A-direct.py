import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = [
        params["demand_2_6"],
        params["demand_6_10"],
        params["demand_10_14"],
        params["demand_14_18"],
        params["demand_18_22"],
        params["demand_22_2"],
    ]
    salary_regular = params["salary_regular"]
    salary_contract = params["salary_contract"]
    shift_length = params["shift_length"]

    periods = list(range(6))
    starts = list(range(6))
    hours_per_period = 24 // 6  # structural: 4-hour periods
    # Number of consecutive periods a shift of shift_length hours covers
    span = int(shift_length // hours_per_period)

    def covers(start, period):
        return any((start + k) % 6 == period for k in range(span))

    model = pyo.ConcreteModel()

    model.Reg = pyo.Var(starts, domain=pyo.NonNegativeIntegers)
    model.Con = pyo.Var(starts, domain=pyo.NonNegativeIntegers)

    def cover_rule(model, period):
        return sum(
            (model.Reg[s] + model.Con[s]) for s in starts if covers(s, period)
        ) >= demand[period]

    model.cover = pyo.Constraint(periods, rule=cover_rule)

    model.total_cost = pyo.Objective(
        expr=shift_length * sum(
            salary_regular * model.Reg[s] + salary_contract * model.Con[s]
            for s in starts
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}