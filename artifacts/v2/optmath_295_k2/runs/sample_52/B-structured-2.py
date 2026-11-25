# IR: {"sets":{"facilities":[0,1,2,3],"customers":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_cost":"fixed_cost[i] from params['fixed_cost'][i]","demand":"demand[j] from params['demand'][j]","capacity":"capacity[i] from params['capacity'][i]","variable_cost":"variable_cost[i,j] from params['variable_cost'][i][j]"},"variables":{"opened[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each customer j: sum_i shipment[i,j] = demand[j].","For each facility i: sum_j shipment[i,j] <= capacity[i] * opened[i]."],"objective":"Minimize sum_i fixed_cost[i] * opened[i] + sum_i,j variable_cost[i,j] * shipment[i,j]."}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 9)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={
            facility: params["fixed_cost"][facility]
            for facility in model.facilities
        },
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={
            customer: params["demand"][customer]
            for customer in model.customers
        },
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={
            facility: params["capacity"][facility]
            for facility in model.facilities
        },
    )
    model.variable_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize={
            (facility, customer): params["variable_cost"][facility][customer]
            for facility in model.facilities
            for customer in model.customers
        },
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(block, customer):
        return (
            sum(
                block.shipment[facility, customer]
                for facility in block.facilities
            )
            == block.demand[customer]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(block, facility):
        return (
            sum(
                block.shipment[facility, customer]
                for customer in block.customers
            )
            <= block.capacity[facility] * block.opened[facility]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[facility] * model.opened[facility]
                for facility in model.facilities
            )
            + sum(
                model.variable_cost[facility, customer]
                * model.shipment[facility, customer]
                for facility in model.facilities
                for customer in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}