# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8,9],"K":[1,2],"E":[[0,1],[0,4],[1,2],[1,3],[1,5],[1,6],[2,3],[3,4],[4,5],[5,6],[5,9],[6,7],[7,8],[7,9],[8,9]],"A":"For each (u,v) in E, include (u,v) then (v,u), preserving E order."},"params":{"capacity[a]":"params['arc_capacity'][position(a)] >= 0","cost[a]":"params['arc_cost'][position(a)]","demand[1]":"params['commodity1_demand'] >= 0","demand[2]":"params['commodity2_demand'] >= 0","source":{"1":1,"2":7},"sink":{"1":4,"2":9}},"variables":{"flow[k,u,v]":"nonnegative continuous, k in K and (u,v) in A"},"constraints":["For each k,n: outgoing flow minus incoming flow equals demand[k] at source[k], -demand[k] at sink[k], and 0 otherwise.","For each k: total outgoing flow at source[k] equals demand[k].","For each k: total incoming flow at sink[k] equals demand[k].","For each (u,v): sum over k of flow[k,u,v] <= capacity[u,v]."],"objective":"Minimize sum over k,(u,v) of cost[u,v]*flow[k,u,v]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    roads = [
        (0, 1),
        (0, 4),
        (1, 2),
        (1, 3),
        (1, 5),
        (1, 6),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (5, 9),
        (6, 7),
        (7, 8),
        (7, 9),
        (8, 9),
    ]
    arcs = [
        directed_arc
        for origin, destination in roads
        for directed_arc in ((origin, destination), (destination, origin))
    ]

    capacities = params["arc_capacity"]
    costs = params["arc_cost"]
    demands = {
        1: params["commodity1_demand"],
        2: params["commodity2_demand"],
    }
    sources = {1: 1, 2: 7}
    sinks = {1: 4, 2: 9}

    if len(capacities) != len(arcs) or len(costs) != len(arcs):
        return {"objective": None, "status": "invalid_arc_data_length"}

    outgoing = {
        node: [(origin, destination) for origin, destination in arcs if origin == node]
        for node in range(10)
    }
    incoming = {
        node: [
            (origin, destination)
            for origin, destination in arcs
            if destination == node
        ]
        for node in range(10)
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=range(10), ordered=True)
    model.K = pyo.Set(initialize=[1, 2], ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.A,
        initialize={
            arc: capacities[position] for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.A,
        initialize={arc: costs[position] for position, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.K, initialize=demands, within=pyo.NonNegativeReals
    )
    model.source = pyo.Param(
        model.K, initialize=sources, within=model.N
    )
    model.sink = pyo.Param(
        model.K, initialize=sinks, within=model.N
    )

    model.flow = pyo.Var(
        model.K, model.A, domain=pyo.NonNegativeReals
    )

    def flow_balance_rule(instance, commodity, node):
        net_supply = (
            instance.demand[commodity]
            if node == sources[commodity]
            else -instance.demand[commodity]
            if node == sinks[commodity]
            else 0
        )
        return (
            sum(
                instance.flow[commodity, origin, destination]
                for origin, destination in outgoing[node]
            )
            - sum(
                instance.flow[commodity, origin, destination]
                for origin, destination in incoming[node]
            )
            == net_supply
        )

    model.flow_balance = pyo.Constraint(
        model.K, model.N, rule=flow_balance_rule
    )

    def source_dispatch_rule(instance, commodity):
        return sum(
            instance.flow[commodity, origin, destination]
            for origin, destination in outgoing[sources[commodity]]
        ) == instance.demand[commodity]

    model.source_dispatch = pyo.Constraint(
        model.K, rule=source_dispatch_rule
    )

    def sink_receipt_rule(instance, commodity):
        return sum(
            instance.flow[commodity, origin, destination]
            for origin, destination in incoming[sinks[commodity]]
        ) == instance.demand[commodity]

    model.sink_receipt = pyo.Constraint(
        model.K, rule=sink_receipt_rule
    )

    def shared_capacity_rule(instance, origin, destination):
        return sum(
            instance.flow[commodity, origin, destination]
            for commodity in instance.K
        ) <= instance.capacity[origin, destination]

    model.shared_capacity = pyo.Constraint(
        model.A, rule=shared_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.flow[commodity, origin, destination]
            for commodity in model.K
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