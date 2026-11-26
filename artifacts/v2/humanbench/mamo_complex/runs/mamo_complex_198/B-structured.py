# IR: {"sets":{"N":[1,2,3,4,5],"E":[[1,3],[1,4],[1,5],[2,3],[2,4],[2,5],[3,4],[3,5],[4,5]],"A":"both directions of every edge in E"},"params":{"cost":"cost_1_3,cost_1_4,cost_1_5,cost_2_3,cost_2_4,cost_2_5,cost_3_4,cost_3_5,cost_4_5; same cost in either direction","supply":"supply_1,supply_2,supply_3,supply_4,supply_5","demand":"demand_1,demand_2,demand_3,demand_4,demand_5"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each i in N: supply[i] + sum(flow[j,i]) - sum(flow[i,j]) >= demand[i]"],"objective":"Minimize sum(cost[i,j]*flow[i,j] for (i,j) in A)","report":"Return the objective rounded to the nearest dollar."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Treat each listed connection as usable in either direction.
    # Cars may remain at their current location or pass through other locations.
    locations = (1, 2, 3, 4, 5)

    edge_costs = {
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }
    supplies = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }
    demands = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    arc_costs = {}
    for (origin, destination), cost in edge_costs.items():
        arc_costs[origin, destination] = cost
        arc_costs[destination, origin] = cost

    model = pyo.ConcreteModel()
    model.locations = pyo.Set(initialize=locations, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=tuple(arc_costs), ordered=True)

    model.unit_cost = pyo.Param(
        model.arcs, initialize=arc_costs, within=pyo.Reals
    )
    model.initial_supply = pyo.Param(
        model.locations, initialize=supplies, within=pyo.NonNegativeReals
    )
    model.required_cars = pyo.Param(
        model.locations, initialize=demands, within=pyo.NonNegativeReals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def demand_balance_rule(instance, location):
        incoming = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if destination == location
        )
        outgoing = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if origin == location
        )
        return (
            instance.initial_supply[location] + incoming - outgoing
            >= instance.required_cars[location]
        )

    model.demand_balance = pyo.Constraint(
        model.locations, rule=demand_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Appsi can raise RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    # Objective retrieval alone determines success; no termination enum checks.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}