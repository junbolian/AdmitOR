# IR: {"sets":[],"params":["demand_A","demand_B","demand_C","supply_A_per_truck","supply_B_per_truck","supply_C_per_truck_A","supply_A_per_truck_B","supply_B_per_truck_B","supply_C_per_truck_B","cost_per_truck_A","cost_per_truck_B"],"variables":{"trucks_A":"nonnegative integer","trucks_B":"nonnegative integer"},"constraints":["supply_A_per_truck*trucks_A + supply_A_per_truck_B*trucks_B >= demand_A","supply_B_per_truck*trucks_A + supply_B_per_truck_B*trucks_B >= demand_B","supply_C_per_truck_A*trucks_A + supply_C_per_truck_B*trucks_B >= demand_C"],"objective":"minimize cost_per_truck_A*trucks_A + cost_per_truck_B*trucks_B"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.demand_A = pyo.Param(initialize=params["demand_A"])
    model.demand_B = pyo.Param(initialize=params["demand_B"])
    model.demand_C = pyo.Param(initialize=params["demand_C"])

    model.supply_A_per_truck = pyo.Param(
        initialize=params["supply_A_per_truck"]
    )
    model.supply_B_per_truck = pyo.Param(
        initialize=params["supply_B_per_truck"]
    )
    model.supply_C_per_truck_A = pyo.Param(
        initialize=params["supply_C_per_truck_A"]
    )
    model.supply_A_per_truck_B = pyo.Param(
        initialize=params["supply_A_per_truck_B"]
    )
    model.supply_B_per_truck_B = pyo.Param(
        initialize=params["supply_B_per_truck_B"]
    )
    model.supply_C_per_truck_B = pyo.Param(
        initialize=params["supply_C_per_truck_B"]
    )

    model.cost_per_truck_A = pyo.Param(
        initialize=params["cost_per_truck_A"]
    )
    model.cost_per_truck_B = pyo.Param(
        initialize=params["cost_per_truck_B"]
    )

    model.trucks_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.trucks_B = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.material_A_requirement = pyo.Constraint(
        expr=(
            model.supply_A_per_truck * model.trucks_A
            + model.supply_A_per_truck_B * model.trucks_B
            >= model.demand_A
        )
    )
    model.material_B_requirement = pyo.Constraint(
        expr=(
            model.supply_B_per_truck * model.trucks_A
            + model.supply_B_per_truck_B * model.trucks_B
            >= model.demand_B
        )
    )
    model.material_C_requirement = pyo.Constraint(
        expr=(
            model.supply_C_per_truck_A * model.trucks_A
            + model.supply_C_per_truck_B * model.trucks_B
            >= model.demand_C
        )
    )

    model.total_cost = pyo.Objective(
        expr=(
            model.cost_per_truck_A * model.trucks_A
            + model.cost_per_truck_B * model.trucks_B
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}