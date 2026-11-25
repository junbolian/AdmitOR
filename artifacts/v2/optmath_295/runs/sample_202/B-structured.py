# IR: {"sets":{"I":[0,1,2,3,4,5],"J":[0,1,2,3,4,5,6,7,8]},"params":{"fixed_costs":"f[i] from params[\"fixed_costs\"]","demands":"d[j] from params[\"demands\"]","shipping_costs":"c[i,j] from params[\"shipping_costs\"]","capacities":"u[i] from params[\"capacities\"]"},"variables":{"opened[i]":"binary, i in I","shipped[i,j]":"continuous nonnegative, (i,j) in I x J"},"constraints":["sum(shipped[i,j] for i in I) == d[j], for each j in J","sum(shipped[i,j] for j in J) <= u[i]*opened[i], for each i in I"],"objective":"minimize sum(f[i]*opened[i] for i in I) + sum(c[i,j]*shipped[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(values, position, prefix):
    """Accept sequences, integer-keyed mappings, or labeled mappings."""
    if isinstance(values, Mapping):
        label = f"{prefix}_{position}"
        if label in values:
            return values[label]
    return values[position]


def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(0, 5)
    model.customers = pyo.RangeSet(0, 8)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={
            i: _entry(fixed_costs, i, "facility")
            for i in model.facilities
        },
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={
            j: _entry(demands, j, "customer")
            for j in model.customers
        },
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize={
            (i, j): _entry(
                _entry(shipping_costs, i, "facility"), j, "customer"
            )
            for i in model.facilities
            for j in model.customers
        },
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={
            i: _entry(capacities, i, "facility")
            for i in model.facilities
        },
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipped[i, j] for i in instance.facilities)
            == instance.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipped[i, j] for j in instance.customers)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_limits = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.shipping_cost[i, j] * model.shipped[i, j]
                for i in model.facilities
                for j in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}