# IR: {"sets":{"weeks":[1,2,3,4],"inventory_periods":[0,1,2,3,4],"holding_weeks":[1,2,3]},"params":{"demand":"weekly demand","capacity":"weekly production capacity","production_cost":"weekly unit production cost","storage_cost":"unit weekly holding cost"},"variables":{"production[weeks]":"nonnegative continuous","inventory[inventory_periods]":"nonnegative continuous"},"constraints":["inventory[0] = 0","inventory[4] = 0","production[t] <= capacity[t] for t in weeks","inventory[t-1] + production[t] = demand[t] + inventory[t] for t in weeks"],"objective":"minimize sum(production_cost[t]*production[t] for t in weeks) + storage_cost*sum(inventory[t] for t in holding_weeks)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Weekly inputs may be length-four sequences ordered by week,
    or mappings keyed by weeks 1 through 4 (integers or strings).
    """

    def weekly_values(values):
        if isinstance(values, Mapping):
            return {
                week: values[week] if week in values else values[str(week)]
                for week in range(1, 5)
            }
        if len(values) != 4:
            raise ValueError("Each weekly input must contain four values.")
        return {week: values[week - 1] for week in range(1, 5)}

    demand = weekly_values(params["demand"])
    capacity = weekly_values(params["capacity"])
    production_cost = weekly_values(params["production_cost"])
    storage_cost = params["storage_cost"]

    model = pyo.ConcreteModel()
    model.weeks = pyo.RangeSet(1, 4)
    model.inventory_periods = pyo.RangeSet(0, 4)
    model.holding_weeks = pyo.RangeSet(1, 3)

    model.demand = pyo.Param(model.weeks, initialize=demand)
    model.capacity = pyo.Param(model.weeks, initialize=capacity)
    model.production_cost = pyo.Param(
        model.weeks, initialize=production_cost
    )
    model.storage_cost = pyo.Param(initialize=storage_cost)

    model.production = pyo.Var(model.weeks, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )
    model.inventory[0].fix(0)
    model.inventory[4].fix(0)

    def capacity_rule(instance, week):
        return instance.production[week] <= instance.capacity[week]

    model.production_limit = pyo.Constraint(
        model.weeks, rule=capacity_rule
    )

    def balance_rule(instance, week):
        return (
            instance.inventory[week - 1] + instance.production[week]
            == instance.demand[week] + instance.inventory[week]
        )

    model.inventory_balance = pyo.Constraint(
        model.weeks, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[week] * model.production[week]
            for week in model.weeks
        )
        + model.storage_cost
        * sum(model.inventory[week] for week in model.holding_weeks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi HiGHS raises this when no feasible solution can be loaded.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}