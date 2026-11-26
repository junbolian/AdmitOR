# IR: {"sets":{},"params":["profit_A1","profit_A2","milk_supply","labor_hours","A1_per_barrel","A2_per_barrel","hours_per_barrel_A1","hours_per_barrel_A2","A1_capacity"],"variables":{"barrels_A1":"continuous >= 0","barrels_A2":"continuous >= 0"},"constraints":["barrels_A1 + barrels_A2 <= milk_supply","hours_per_barrel_A1*barrels_A1 + hours_per_barrel_A2*barrels_A2 <= labor_hours","A1_per_barrel*barrels_A1 <= A1_capacity"],"objective":"maximize profit_A1*A1_per_barrel*barrels_A1 + profit_A2*A2_per_barrel*barrels_A2"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.profit_A1 = pyo.Param(initialize=params["profit_A1"])
    model.profit_A2 = pyo.Param(initialize=params["profit_A2"])
    model.milk_supply = pyo.Param(initialize=params["milk_supply"])
    model.labor_hours = pyo.Param(initialize=params["labor_hours"])
    model.A1_per_barrel = pyo.Param(initialize=params["A1_per_barrel"])
    model.A2_per_barrel = pyo.Param(initialize=params["A2_per_barrel"])
    model.hours_per_barrel_A1 = pyo.Param(
        initialize=params["hours_per_barrel_A1"]
    )
    model.hours_per_barrel_A2 = pyo.Param(
        initialize=params["hours_per_barrel_A2"]
    )
    model.A1_capacity = pyo.Param(initialize=params["A1_capacity"])

    model.barrels_A1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.barrels_A2 = pyo.Var(domain=pyo.NonNegativeReals)

    model.milk_limit = pyo.Constraint(
        expr=model.barrels_A1 + model.barrels_A2 <= model.milk_supply
    )
    model.labor_limit = pyo.Constraint(
        expr=(
            model.hours_per_barrel_A1 * model.barrels_A1
            + model.hours_per_barrel_A2 * model.barrels_A2
            <= model.labor_hours
        )
    )
    model.type_A_limit = pyo.Constraint(
        expr=model.A1_per_barrel * model.barrels_A1 <= model.A1_capacity
    )

    model.total_profit = pyo.Objective(
        expr=(
            model.profit_A1 * model.A1_per_barrel * model.barrels_A1
            + model.profit_A2 * model.A2_per_barrel * model.barrels_A2
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}