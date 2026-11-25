# IR: {"sets":{"facilities":"0..4","customers":"0..5"},"params":{"fixed_cost":"[facility]","demand":"[customer]","capacity":"[facility]","serving_cost":"[customer][facility]"},"variables":{"opened[facility]":"Binary","shipment[customer,facility]":"NonNegativeReals"},"constraints":["For each customer: sum_facility shipment[customer,facility] = demand[customer]","For each facility: sum_customer shipment[customer,facility] <= capacity[facility] * opened[facility]"],"objective":"Minimize sum_facility fixed_cost[facility] * opened[facility] + sum_customer,facility serving_cost[customer][facility] * shipment[customer,facility]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 4)
    model.customers = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda _, facility: params["fixed_cost"][facility],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda _, customer: params["demand"][customer],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda _, facility: params["capacity"][facility],
        within=pyo.NonNegativeReals,
    )
    model.serving_cost = pyo.Param(
        model.customers,
        model.facilities,
        initialize=lambda _, customer, facility: params["serving_cost"][customer][facility],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.customers, model.facilities, domain=pyo.NonNegativeReals
    )

    def demand_rule(problem, customer):
        return (
            sum(
                problem.shipment[customer, facility]
                for facility in problem.facilities
            )
            == problem.demand[customer]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(problem, facility):
        return (
            sum(
                problem.shipment[customer, facility]
                for customer in problem.customers
            )
            <= problem.capacity[facility] * problem.opened[facility]
        )

    model.capacity_link = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[facility] * model.opened[facility]
            for facility in model.facilities
        )
        + sum(
            model.serving_cost[customer, facility]
            * model.shipment[customer, facility]
            for customer in model.customers
            for facility in model.facilities
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}