# IR: {"sets":{"I":"range(params['num_centers'])","J":"range(params['num_stores'])"},"params":{"num_centers":"cardinality of I","num_stores":"cardinality of J","opening_costs":"fixed opening costs indexed by I","transportation_costs":"shipping costs indexed by I,J; accept a nested matrix, a flat row-major sequence, or a mapping keyed by (i,j)","demands":"store demands indexed by J","capacities":"center capacities indexed by I"},"variables":{"opened[i]":"binary for i in I","shipped[i,j]":"nonnegative continuous for (i,j) in I x J"},"constraints":["For each j in J: sum(shipped[i,j] for i in I) == demands[j]","For each i in I: sum(shipped[i,j] for j in J) <= capacities[i] * opened[i]"],"objective":"Minimize sum(opening_costs[i]*opened[i] for i in I) + sum(transportation_costs[i,j]*shipped[i,j] for (i,j) in I x J)"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]
    opening_costs = params["opening_costs"]
    transportation_costs = params["transportation_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    def transportation_cost_at(i, j):
        if (
            isinstance(transportation_costs, Mapping)
            and (i, j) in transportation_costs
        ):
            return transportation_costs[i, j]

        row_or_value = transportation_costs[i]
        if isinstance(row_or_value, Number):
            return transportation_costs[i * num_stores + j]

        return row_or_value[j]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=range(num_centers), ordered=True)
    model.stores = pyo.Set(initialize=range(num_stores), ordered=True)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: opening_costs[i] for i in range(num_centers)},
    )
    model.transportation_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transportation_cost_at(i, j)
            for i in range(num_centers)
            for j in range(num_stores)
        },
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in range(num_stores)},
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacities[i] for i in range(num_centers)},
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(current_model, j):
        return (
            sum(current_model.shipped[i, j] for i in current_model.centers)
            == current_model.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(current_model, i):
        return (
            sum(current_model.shipped[i, j] for j in current_model.stores)
            <= current_model.center_capacity[i] * current_model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[i] * model.opened[i]
            for i in model.centers
        )
        + sum(
            model.transportation_cost[i, j] * model.shipped[i, j]
            for i in model.centers
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi can raise when no feasible solution is available to load.
        # Success is determined only by objective retrieval below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}