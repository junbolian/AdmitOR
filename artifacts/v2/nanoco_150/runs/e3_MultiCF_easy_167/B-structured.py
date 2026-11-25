# IR: {"sets":{"N":"0..9","K":[1,2],"A":[[0,1],[1,0],[0,5],[5,0],[0,7],[7,0],[0,8],[8,0],[0,9],[9,0],[1,2],[2,1],[2,3],[3,2],[2,9],[9,2],[3,4],[4,3],[4,5],[5,4],[5,6],[6,5],[6,7],[7,6],[6,9],[9,6],[7,8],[8,7],[8,9],[9,8]]},"params":{"capacity[a]":"params['arc_capacity'][position(a)]","cost[a]":"params['arc_cost'][position(a)]","demand[1]":"params['demand_commodity_1']","demand[2]":"params['demand_commodity_2']","source":{"1":5,"2":3},"sink":{"1":4,"2":0}},"variables":{"flow[k,i,j]":"nonnegative real, k in K, (i,j) in A"},"constraints":["For each k,n: outgoing(k,n)-incoming(k,n)=demand[k] if n=source[k], -demand[k] if n=sink[k], else 0.","For each k: outgoing(k,source[k])=demand[k].","For each k: incoming(k,sink[k])=demand[k].","For each (i,j): sum_k flow[k,i,j]<=capacity[i,j]."],"objective":"Minimize sum_{k,(i,j)} cost[i,j]*flow[k,i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (1, 0),
        (0, 5), (5, 0),
        (0, 7), (7, 0),
        (0, 8), (8, 0),
        (0, 9), (9, 0),
        (1, 2), (2, 1),
        (2, 3), (3, 2),
        (2, 9), (9, 2),
        (3, 4), (4, 3),
        (4, 5), (5, 4),
        (5, 6), (6, 5),
        (6, 7), (7, 6),
        (6, 9), (9, 6),
        (7, 8), (8, 7),
        (8, 9), (9, 8),
    ]
    nodes = range(10)
    commodities = (1, 2)
    sources = {1: 5, 2: 3}
    sinks = {1: 4, 2: 0}

    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    demands = {
        1: params["demand_commodity_1"],
        2: params["demand_commodity_2"],
    }

    if len(arc_capacity) != len(arcs) or len(arc_cost) != len(arcs):
        raise ValueError("arc_capacity and arc_cost must each contain 30 entries.")

    outgoing = {
        node: [arc for arc in arcs if arc[0] == node]
        for node in nodes
    }
    incoming = {
        node: [arc for arc in arcs if arc[1] == node]
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.K = pyo.Set(initialize=commodities, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.A,
        initialize={
            arc: arc_capacity[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.A,
        initialize={
            arc: arc_cost[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.K,
        initialize=demands,
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.K,
        model.A,
        domain=pyo.NonNegativeReals,
    )

    def balance_rule(block, commodity, node):
        net_outflow = (
            sum(block.flow[commodity, i, j] for i, j in outgoing[node])
            - sum(block.flow[commodity, i, j] for i, j in incoming[node])
        )
        if node == sources[commodity]:
            return net_outflow == block.demand[commodity]
        if node == sinks[commodity]:
            return net_outflow == -block.demand[commodity]
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.K, model.N, rule=balance_rule
    )

    def source_rule(block, commodity):
        return sum(
            block.flow[commodity, i, j]
            for i, j in outgoing[sources[commodity]]
        ) == block.demand[commodity]

    model.source_outflow = pyo.Constraint(model.K, rule=source_rule)

    def sink_rule(block, commodity):
        return sum(
            block.flow[commodity, i, j]
            for i, j in incoming[sinks[commodity]]
        ) == block.demand[commodity]

    model.sink_inflow = pyo.Constraint(model.K, rule=sink_rule)

    def capacity_rule(block, i, j):
        return sum(
            block.flow[commodity, i, j]
            for commodity in block.K
        ) <= block.capacity[i, j]

    model.shared_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[commodity, i, j]
            for commodity in model.K
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}