# IR: {"sets":{"N":[1,2,3,4,5],"E":"{(i,j): i,j in N, i<j}","A":"{(i,j): i,j in N, i!=j}"},"params":{"cost":"E -> cost_i_j from params; applies in both directions","supply":"N -> supply_i from params","demand":"N -> demand_i from params"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each i in N: supply[i] + sum(flow[j,i] for j!=i) - sum(flow[i,j] for j!=i) >= demand[i]"],"objective":"Minimize sum(cost[min(i,j),max(i,j)] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize relocation costs, assuming each route permits both directions."""
    locations = (1, 2, 3, 4, 5)
    edges = tuple(
        (i, j) for i in locations for j in locations if i < j
    )
    arcs = tuple(
        (i, j) for i in locations for j in locations if i != j
    )

    cost_data = {
        (1, 2): params["cost_1_2"],
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
    supply_data = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }
    demand_data = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=locations, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.route_cost = pyo.Param(model.routes, initialize=cost_data)
    model.initial_supply = pyo.Param(model.regions, initialize=supply_data)
    model.required_cars = pyo.Param(model.regions, initialize=demand_data)

    # The network-flow LP admits integral optimal flows for integral supplies
    # and demands, so explicit integer restrictions are unnecessary.
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def needs_met_rule(instance, i):
        incoming = sum(
            instance.flow[j, i] for j in instance.regions if j != i
        )
        outgoing = sum(
            instance.flow[i, j] for j in instance.regions if j != i
        )
        return (
            instance.initial_supply[i] + incoming - outgoing
            >= instance.required_cars[i]
        )

    model.needs_met = pyo.Constraint(
        model.regions, rule=needs_met_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[min(i, j), max(i, j)] * model.flow[i, j]
            for i, j in model.arcs
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