# IR: {"sets":{"years":[1,2,3]},"params":["fund","project1_rate","project2_return","project2_cap","project3_return","project3_cap","project4_return","project4_cap"],"variables":{"annual[years]":"continuous >= 0; project (1) investment at each year's start","second":"continuous >= 0; project (2) investment at year 1 start","third":"continuous >= 0; project (3) investment at year 2 start","fourth":"continuous >= 0; project (4) investment at year 3 start","cash[years]":"continuous >= 0; uninvested cash held during each year"},"constraints":["annual[1] + second + cash[1] = fund","annual[2] + third + cash[2] = (1 + project1_rate)*annual[1] + cash[1]","annual[3] + fourth + cash[3] = (1 + project1_rate)*annual[2] + project2_return*second + project3_return*third + cash[2]","second <= project2_cap","third <= project3_cap","fourth <= project4_cap"],"objective":"maximize (1 + project1_rate)*annual[3] + project4_return*fourth + cash[3]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fund = params["fund"]
    project1_rate = params["project1_rate"]
    project2_return = params["project2_return"]
    project2_cap = params["project2_cap"]
    project3_return = params["project3_return"]
    project3_cap = params["project3_cap"]
    project4_return = params["project4_return"]
    project4_cap = params["project4_cap"]

    model = pyo.ConcreteModel()
    model.years = pyo.RangeSet(1, 3)

    model.annual = pyo.Var(model.years, domain=pyo.NonNegativeReals)
    model.second = pyo.Var(domain=pyo.NonNegativeReals)
    model.third = pyo.Var(domain=pyo.NonNegativeReals)
    model.fourth = pyo.Var(domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.years, domain=pyo.NonNegativeReals)

    model.year1_balance = pyo.Constraint(
        expr=model.annual[1] + model.second + model.cash[1] == fund
    )
    model.year2_balance = pyo.Constraint(
        expr=model.annual[2] + model.third + model.cash[2]
        == (1 + project1_rate) * model.annual[1] + model.cash[1]
    )
    model.year3_balance = pyo.Constraint(
        expr=model.annual[3] + model.fourth + model.cash[3]
        == (
            (1 + project1_rate) * model.annual[2]
            + project2_return * model.second
            + project3_return * model.third
            + model.cash[2]
        )
    )

    model.project2_limit = pyo.Constraint(
        expr=model.second <= project2_cap
    )
    model.project3_limit = pyo.Constraint(
        expr=model.third <= project3_cap
    )
    model.project4_limit = pyo.Constraint(
        expr=model.fourth <= project4_cap
    )

    model.final_wealth = pyo.Objective(
        expr=(
            (1 + project1_rate) * model.annual[3]
            + project4_return * model.fourth
            + model.cash[3]
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.final_wealth))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}