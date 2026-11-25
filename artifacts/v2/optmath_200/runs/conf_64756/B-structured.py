# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4]},"params":{"production_cost":"products x periods","setup_cost":"products x periods","holding_cost":"products x periods","cumulative_demand":"products x periods","resource_capacity":"periods","resource_consumption":"products","max_production_if_setup":"products x periods"},"variables":{"production":"nonnegative continuous, products x periods","inventory":"nonnegative continuous, products x periods","setup":"binary, products x periods"},"constraints":["For each product i and period t: sum(production[i,s] for s <= t) - inventory[i,t] = cumulative_demand[i,t] (zero inventory before period 0).","For each period t: sum(resource_consumption[i] * production[i,t] for i) <= resource_capacity[t].","For each product i and period t: production[i,t] <= max_production_if_setup[i,t] * setup[i,t].","For each product i: inventory[i,0] = 0 and inventory[i,4] = 0."],"objective":"Minimize sum(production_cost[i,t]*production[i,t] + setup_cost[i,t]*setup[i,t] + holding_cost[i,t]*inventory[i,t] for all i,t)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
from collections.abc import Mapping


def _entry(data, *indices):
    """Read arrays, nested mappings, or tuple-indexed mappings."""
    if len(indices) > 1 and isinstance(data, Mapping):
        if indices in data:
            return data[indices]
    result = data
    for idx in indices:
        if isinstance(result, Mapping):
            result = result[idx] if idx in result else result[str(idx)]
        else:
            result = result[idx]
    return result


def solve(params):
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    cumulative_demand = params["cumulative_demand"]
    resource_capacity = params["resource_capacity"]
    resource_consumption = params["resource_consumption"]
    max_production_if_setup = params["max_production_if_setup"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)

    model.production_cost = pyo.Param(
        model.products, model.periods,
        initialize=lambda mdl, i, t: _entry(production_cost, i, t),
    )
    model.setup_cost = pyo.Param(
        model.products, model.periods,
        initialize=lambda mdl, i, t: _entry(setup_cost, i, t),
    )
    model.holding_cost = pyo.Param(
        model.products, model.periods,
        initialize=lambda mdl, i, t: _entry(holding_cost, i, t),
    )
    model.cumulative_demand = pyo.Param(
        model.products, model.periods,
        initialize=lambda mdl, i, t: _entry(cumulative_demand, i, t),
    )
    model.resource_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, t: _entry(resource_capacity, t),
    )
    model.resource_consumption = pyo.Param(
        model.products,
        initialize=lambda mdl, i: _entry(resource_consumption, i),
    )
    model.max_production_if_setup = pyo.Param(
        model.products, model.periods,
        initialize=lambda mdl, i, t: _entry(max_production_if_setup, i, t),
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.periods, domain=pyo.Binary
    )

    def demand_balance_rule(mdl, i, t):
        return (
            sum(mdl.production[i, s] for s in mdl.periods if s <= t)
            - mdl.inventory[i, t]
            == mdl.cumulative_demand[i, t]
        )

    model.demand_balance = pyo.Constraint(
        model.products, model.periods, rule=demand_balance_rule
    )

    def capacity_rule(mdl, t):
        return sum(
            mdl.resource_consumption[i] * mdl.production[i, t]
            for i in mdl.products
        ) <= mdl.resource_capacity[t]

    model.capacity_limit = pyo.Constraint(model.periods, rule=capacity_rule)

    model.setup_link = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, i, t: (
            mdl.production[i, t]
            <= mdl.max_production_if_setup[i, t] * mdl.setup[i, t]
        ),
    )

    model.initial_inventory_zero = pyo.Constraint(
        model.products, rule=lambda mdl, i: mdl.inventory[i, 0] == 0
    )
    model.final_inventory_zero = pyo.Constraint(
        model.products, rule=lambda mdl, i: mdl.inventory[i, 4] == 0
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[i, t] * model.production[i, t]
            + model.setup_cost[i, t] * model.setup[i, t]
            + model.holding_cost[i, t] * model.inventory[i, t]
            for i in model.products
            for t in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}