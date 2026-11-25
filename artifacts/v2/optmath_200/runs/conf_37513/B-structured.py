# IR: {"sets":{"P":[0,1],"L":[0,1],"A":[[0,1],[1,0]]},"params":["cost_p0_0_1","cost_p0_1_0","cost_p1_0_1","cost_p1_1_0","capacity_p0","capacity_p1","demand_1_0","avail_p0","avail_p1","max_deploy_1_0"],"variables":{"deploy[p,i,j]":"nonnegative integer, p in P, (i,j) in A","idle[p,i]":"nonnegative integer, p in P, i in L","initial_idle[p,i]":"nonnegative integer, p in P, i in L"},"constraints":["initial_idle[p,i] = idle[p,i] + sum(deploy[p,i,j] for (i,j) in A), for p in P, i in L","sum(idle[p,i] for i in L) <= availability[p], for p in P","sum(capacity[p]*deploy[p,1,0] for p in P) >= demand_1_0","deploy[p,0,1] = 0, for p in P","deploy[p,1,0] <= max_deploy_1_0, for p in P"],"objective":"minimize sum(cost[p,i,j]*deploy[p,i,j] for p in P, (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (0, 0, 1): params["cost_p0_0_1"],
        (0, 1, 0): params["cost_p0_1_0"],
        (1, 0, 1): params["cost_p1_0_1"],
        (1, 1, 0): params["cost_p1_1_0"],
    }
    capacities = {
        0: params["capacity_p0"],
        1: params["capacity_p1"],
    }
    availability = {
        0: params["avail_p0"],
        1: params["avail_p1"],
    }
    demand = params["demand_1_0"]
    deployment_limit = params["max_deploy_1_0"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=[0, 1])
    model.L = pyo.Set(initialize=[0, 1])
    model.A = pyo.Set(dimen=2, initialize=[(0, 1), (1, 0)])

    model.cost = pyo.Param(model.P, model.A, initialize=costs)
    model.capacity = pyo.Param(model.P, initialize=capacities)
    model.availability = pyo.Param(model.P, initialize=availability)
    model.route_demand = pyo.Param(initialize=demand)
    model.deployment_limit = pyo.Param(initialize=deployment_limit)

    model.deploy = pyo.Var(model.P, model.A, domain=pyo.NonNegativeIntegers)
    model.idle = pyo.Var(model.P, model.L, domain=pyo.NonNegativeIntegers)
    model.initial_idle = pyo.Var(
        model.P, model.L, domain=pyo.NonNegativeIntegers
    )

    def balance_rule(block, plane, location):
        return block.initial_idle[plane, location] == (
            block.idle[plane, location]
            + sum(
                block.deploy[plane, origin, destination]
                for origin, destination in block.A
                if origin == location
            )
        )

    model.idle_balance = pyo.Constraint(model.P, model.L, rule=balance_rule)

    def availability_rule(block, plane):
        return (
            sum(block.idle[plane, location] for location in block.L)
            <= block.availability[plane]
        )

    model.idle_availability = pyo.Constraint(
        model.P, rule=availability_rule
    )

    model.passenger_requirement = pyo.Constraint(
        expr=sum(
            model.capacity[plane] * model.deploy[plane, 1, 0]
            for plane in model.P
        )
        >= model.route_demand
    )

    model.forbidden_route = pyo.Constraint(
        model.P,
        rule=lambda block, plane: block.deploy[plane, 0, 1] == 0,
    )
    model.return_route_limit = pyo.Constraint(
        model.P,
        rule=lambda block, plane: (
            block.deploy[plane, 1, 0] <= block.deployment_limit
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[plane, origin, destination]
            * model.deploy[plane, origin, destination]
            for plane in model.P
            for origin, destination in model.A
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