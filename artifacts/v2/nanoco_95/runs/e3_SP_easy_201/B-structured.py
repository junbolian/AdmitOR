# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7,8,9],"arcs":[[0,1],[0,7],[1,2],[1,7],[2,3],[2,6],[3,4],[3,5],[3,8],[3,9],[4,5],[4,8],[5,6],[6,7],[7,8],[7,9],[8,9]]},"params":{"cost[i,j]":"params['arc_cost_i_j'] for each arc (i,j)","supply[0]":"params['supply_source']","supply[9]":"-params['demand_sink']","supply[1..8]":"params['intermediate_supply']"},"variables":{"flow[i,j]":{"type":"NonNegativeReals","bounds":[0,1],"index":"arcs"}},"constraints":["For each node n: sum(flow[n,j] for outgoing arcs) - sum(flow[i,n] for incoming arcs) = supply[n]."],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * flow[i,j] for (i,j) in arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 7),
        (1, 2), (1, 7),
        (2, 3), (2, 6),
        (3, 4), (3, 5), (3, 8), (3, 9),
        (4, 5), (4, 8),
        (5, 6),
        (6, 7),
        (7, 8), (7, 9),
        (8, 9),
    )

    costs = {
        (0, 1): params["arc_cost_0_1"],
        (0, 7): params["arc_cost_0_7"],
        (1, 2): params["arc_cost_1_2"],
        (1, 7): params["arc_cost_1_7"],
        (2, 3): params["arc_cost_2_3"],
        (2, 6): params["arc_cost_2_6"],
        (3, 4): params["arc_cost_3_4"],
        (3, 5): params["arc_cost_3_5"],
        (3, 8): params["arc_cost_3_8"],
        (3, 9): params["arc_cost_3_9"],
        (4, 5): params["arc_cost_4_5"],
        (4, 8): params["arc_cost_4_8"],
        (5, 6): params["arc_cost_5_6"],
        (6, 7): params["arc_cost_6_7"],
        (7, 8): params["arc_cost_7_8"],
        (7, 9): params["arc_cost_7_9"],
        (8, 9): params["arc_cost_8_9"],
    }

    supplies = {
        node: params["intermediate_supply"]
        for node in range(1, 9)
    }
    supplies[0] = params["supply_source"]
    supplies[9] = -params["demand_sink"]

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in range(10)
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in range(10)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.arc_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.net_supply = pyo.Param(
        model.nodes, initialize=supplies, within=pyo.Reals
    )
    model.flow = pyo.Var(
        model.arcs, domain=pyo.NonNegativeReals, bounds=(0, 1)
    )

    def balance_rule(instance, node):
        return (
            sum(instance.flow[arc] for arc in outgoing[node])
            - sum(instance.flow[arc] for arc in incoming[node])
            == instance.net_supply[node]
        )

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}