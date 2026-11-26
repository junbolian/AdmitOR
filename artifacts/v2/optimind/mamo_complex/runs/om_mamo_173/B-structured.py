# IR: {"sets":{"F":"{1,...,7}","A":"{(i,j) in F x F: i != j}"},"params":{"initial_supply":"params['initial_supply'][i-1]","required_demand":"params['required_demand'][i-1]","transfer_cost":"params['transfer_cost'][i-1][position of j in ascending F excluding i]"},"variables":{"transfer[i,j]":{"index":"A","type":"NonNegativeReals"},"supply_used[i]":{"index":"F","type":"NonNegativeReals"}},"constraints":["supply_used[i] <= initial_supply[i], for i in F","supply_used[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) == required_demand[i], for i in F"],"objective":{"sense":"minimize","expression":"sum(transfer_cost[i,j] * transfer[i,j] for (i,j) in A)"}}
#
# Modeling assumption: initial_supply represents available inventory; surplus
# may remain unused in reserve. Exact demand applies to inventory committed
# to meeting requirements. Requiring all available inventory to be committed
# would make the supplied instance infeasible because total supply exceeds
# total demand.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = tuple(range(1, 8))
    arcs = tuple(
        (origin, destination)
        for origin in facilities
        for destination in facilities
        if origin != destination
    )

    initial_supply = {
        facility: params["initial_supply"][facility - 1]
        for facility in facilities
    }
    required_demand = {
        facility: params["required_demand"][facility - 1]
        for facility in facilities
    }
    transfer_cost = {
        (origin, destination): params["transfer_cost"][origin - 1][position]
        for origin in facilities
        for position, destination in enumerate(
            other for other in facilities if other != origin
        )
    }

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.initial_supply = pyo.Param(
        model.facilities,
        initialize=initial_supply,
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.facilities,
        initialize=required_demand,
        within=pyo.NonNegativeReals,
    )
    model.transfer_cost = pyo.Param(
        model.arcs,
        initialize=transfer_cost,
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.supply_used = pyo.Var(
        model.facilities, domain=pyo.NonNegativeReals
    )

    def availability_rule(problem, facility):
        return (
            problem.supply_used[facility]
            <= problem.initial_supply[facility]
        )

    model.supply_availability = pyo.Constraint(
        model.facilities, rule=availability_rule
    )

    def balance_rule(problem, facility):
        incoming = sum(
            problem.transfer[origin, facility]
            for origin in problem.facilities
            if origin != facility
        )
        outgoing = sum(
            problem.transfer[facility, destination]
            for destination in problem.facilities
            if destination != facility
        )
        return (
            problem.supply_used[facility] + incoming - outgoing
            == problem.required_demand[facility]
        )

    model.demand_balance = pyo.Constraint(
        model.facilities, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transfer_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}