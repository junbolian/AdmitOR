# IR: {"sets":{"F":"range(params['num_facilities'])","D":"range(params['num_dcs'])","A":"F x D"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost_i_j'] for every (i,j) in A","capacity":"params['cap_i_j'] for every (i,j) in A"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum_j shipment[i,j] == supply[i] for each i in F","sum_i shipment[i,j] == demand[j] for each j in D","shipment[i,j] <= capacity[i,j] for each (i,j) in A"],"objective":"minimize sum_(i,j) cost[i,j] * shipment[i,j]"}
#
# The listed parameters do not fully specify this optimization problem:
# an 8-by-10 network needs 80 costs and 80 capacities, but only four of
# each are provided. The omitted LP data cannot be reconstructed from
# these examples. Assigning zero costs, unlimited capacities, or forbidden
# routes would change the problem.
#
# This script solves the stated model when the omitted cost_i_j and
# cap_i_j entries are supplied. Otherwise it reports incomplete input;
# there is no justified numerical optimum for the supplied data alone.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    num_dcs = params["num_dcs"]
    supply = params["supply"]
    demand = params["demand"]

    costs = {
        (0, 0): params["cost_0_0"],
        (0, 1): params["cost_0_1"],
        (1, 0): params["cost_1_0"],
        (2, 9): params["cost_2_9"],
    }
    capacities = {
        (0, 0): params["cap_0_0"],
        (0, 1): params["cap_0_1"],
        (1, 0): params["cap_1_0"],
        (2, 9): params["cap_2_9"],
    }

    facilities = range(num_facilities)
    dcs = range(num_dcs)
    routes = [(facility, dc) for facility in facilities for dc in dcs]

    for facility, dc in routes:
        cost_key = f"cost_{facility}_{dc}"
        capacity_key = f"cap_{facility}_{dc}"
        if cost_key not in params or capacity_key not in params:
            return {"objective": None, "status": "incomplete_input"}
        costs[facility, dc] = params[cost_key]
        capacities[facility, dc] = params[capacity_key]

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.dcs = pyo.Set(initialize=dcs, ordered=True)

    model.available_supply = pyo.Param(
        model.facilities,
        initialize={facility: supply[facility] for facility in facilities},
    )
    model.required_demand = pyo.Param(
        model.dcs,
        initialize={dc: demand[dc] for dc in dcs},
    )
    model.transport_cost = pyo.Param(
        model.facilities, model.dcs, initialize=costs
    )
    model.route_capacity = pyo.Param(
        model.facilities, model.dcs, initialize=capacities
    )

    model.shipment = pyo.Var(
        model.facilities, model.dcs, domain=pyo.NonNegativeReals
    )

    def supply_rule(mod, facility):
        return (
            sum(mod.shipment[facility, dc] for dc in mod.dcs)
            == mod.available_supply[facility]
        )

    def demand_rule(mod, dc):
        return (
            sum(mod.shipment[facility, dc] for facility in mod.facilities)
            == mod.required_demand[dc]
        )

    def capacity_rule(mod, facility, dc):
        return mod.shipment[facility, dc] <= mod.route_capacity[facility, dc]

    model.supply_balance = pyo.Constraint(
        model.facilities, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(model.dcs, rule=demand_rule)
    model.capacity_limits = pyo.Constraint(
        model.facilities, model.dcs, rule=capacity_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[facility, dc] * model.shipment[facility, dc]
            for facility, dc in routes
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