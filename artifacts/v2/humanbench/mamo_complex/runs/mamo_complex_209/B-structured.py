# IR: {"sets":{"Q":[1,2,3,4]},"params":["regular_cost","overtime_cost","holding_cost","regular_capacity","initial_inventory","demand"],"variables":{"regular[Q]":"NonNegativeReals","overtime[Q]":"NonNegativeReals","inventory[Q]":"NonNegativeReals"},"constraints":["regular[q] <= regular_capacity for q in Q","inventory[q] = (initial_inventory if q == 1 else inventory[q-1]) + regular[q] + overtime[q] - demand[q] for q in Q"],"objective":"minimize sum(regular_cost*regular[q] + overtime_cost*overtime[q] + holding_cost*inventory[q] for q in Q)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the four-quarter LP; demand may be a sequence or quarter-keyed mapping."""
    demand_input = params["demand"]
    if isinstance(demand_input, Mapping):
        demand_by_quarter = {
            quarter: (
                demand_input[quarter]
                if quarter in demand_input
                else demand_input[str(quarter)]
            )
            for quarter in range(1, 5)
        }
    else:
        if len(demand_input) != 4:
            raise ValueError("demand must contain exactly four quarterly values.")
        demand_by_quarter = {
            quarter: demand_input[quarter - 1] for quarter in range(1, 5)
        }

    model = pyo.ConcreteModel()
    model.quarters = pyo.RangeSet(1, 4)

    model.regular_cost = pyo.Param(
        initialize=params["regular_cost"], within=pyo.Reals
    )
    model.overtime_cost = pyo.Param(
        initialize=params["overtime_cost"], within=pyo.Reals
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost"], within=pyo.Reals
    )
    model.regular_capacity = pyo.Param(
        initialize=params["regular_capacity"], within=pyo.NonNegativeReals
    )
    model.initial_inventory = pyo.Param(
        initialize=params["initial_inventory"], within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.quarters,
        initialize=demand_by_quarter,
        within=pyo.NonNegativeReals,
    )

    model.regular = pyo.Var(model.quarters, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.quarters, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.quarters, domain=pyo.NonNegativeReals)

    def regular_capacity_rule(block, quarter):
        return block.regular[quarter] <= block.regular_capacity

    model.regular_capacity_limit = pyo.Constraint(
        model.quarters, rule=regular_capacity_rule
    )

    def inventory_balance_rule(block, quarter):
        beginning_inventory = (
            block.initial_inventory
            if quarter == 1
            else block.inventory[quarter - 1]
        )
        return block.inventory[quarter] == (
            beginning_inventory
            + block.regular[quarter]
            + block.overtime[quarter]
            - block.demand[quarter]
        )

    model.inventory_balance = pyo.Constraint(
        model.quarters, rule=inventory_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.regular_cost * model.regular[quarter]
            + model.overtime_cost * model.overtime[quarter]
            + model.holding_cost * model.inventory[quarter]
            for quarter in model.quarters
        ),
        sense=pyo.minimize,
    )

    # APPsi raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    # Success depends solely on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}