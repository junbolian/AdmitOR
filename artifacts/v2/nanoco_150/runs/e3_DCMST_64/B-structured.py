# IR: {"sets":{"V":"{1,...,num_branches}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j),(j,i): (i,j) in E}"},"params":{"num_branches":"params['num_branches']; frozen index-set size","max_degree":"params['max_degree']","cost[i,j]":"corresponding cost parameter from params for each (i,j) in E"},"variables":{"selected[i,j]":"Binary for (i,j) in E","flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["sum(selected[i,j] for (i,j) in E) = num_branches-1","sum(selected[min(v,u),max(v,u)] for u in V if u!=v) <= max_degree for v in V","flow[i,j] <= (num_branches-1)*selected[min(i,j),max(i,j)] for (i,j) in A","sum(flow[v,u]-flow[u,v] for u in V if u!=v) = num_branches-1 if v=1 else -1 for v in V"],"objective":"minimize sum(cost[i,j]*selected[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_branches = params["num_branches"]
    max_degree = params["max_degree"]

    costs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (1, 5): params["cost_15"],
        (1, 6): params["cost_16"],
        (1, 7): params["cost_17"],
        (1, 8): params["cost_18"],
        (1, 9): params["cost_19"],
        (1, 10): params["cost_1_10"],
        (1, 11): params["cost_1_11"],
        (1, 12): params["cost_1_12"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (2, 5): params["cost_25"],
        (2, 6): params["cost_26"],
        (2, 7): params["cost_27"],
        (2, 8): params["cost_28"],
        (2, 9): params["cost_29"],
        (2, 10): params["cost_2_10"],
        (2, 11): params["cost_2_11"],
        (2, 12): params["cost_2_12"],
        (3, 4): params["cost_34"],
        (3, 5): params["cost_35"],
        (3, 6): params["cost_36"],
        (3, 7): params["cost_37"],
        (3, 8): params["cost_38"],
        (3, 9): params["cost_39"],
        (3, 10): params["cost_3_10"],
        (3, 11): params["cost_3_11"],
        (3, 12): params["cost_3_12"],
        (4, 5): params["cost_45"],
        (4, 6): params["cost_46"],
        (4, 7): params["cost_47"],
        (4, 8): params["cost_48"],
        (4, 9): params["cost_49"],
        (4, 10): params["cost_4_10"],
        (4, 11): params["cost_4_11"],
        (4, 12): params["cost_4_12"],
        (5, 6): params["cost_56"],
        (5, 7): params["cost_57"],
        (5, 8): params["cost_58"],
        (5, 9): params["cost_59"],
        (5, 10): params["cost_5_10"],
        (5, 11): params["cost_5_11"],
        (5, 12): params["cost_5_12"],
        (6, 7): params["cost_67"],
        (6, 8): params["cost_68"],
        (6, 9): params["cost_69"],
        (6, 10): params["cost_6_10"],
        (6, 11): params["cost_6_11"],
        (6, 12): params["cost_6_12"],
        (7, 8): params["cost_78"],
        (7, 9): params["cost_79"],
        (7, 10): params["cost_7_10"],
        (7, 11): params["cost_7_11"],
        (7, 12): params["cost_7_12"],
        (8, 9): params["cost_89"],
        (8, 10): params["cost_8_10"],
        (8, 11): params["cost_8_11"],
        (8, 12): params["cost_8_12"],
        (9, 10): params["cost_9_10"],
        (9, 11): params["cost_9_11"],
        (9, 12): params["cost_9_12"],
        (10, 11): params["cost_10_11"],
        (10, 12): params["cost_10_12"],
        (11, 12): params["cost_11_12"],
    }

    model = pyo.ConcreteModel()
    model.branch_count = pyo.Param(
        initialize=num_branches, within=pyo.PositiveIntegers
    )
    model.degree_limit = pyo.Param(initialize=max_degree, within=pyo.Reals)
    model.V = pyo.RangeSet(1, num_branches)

    edges = [(i, j) for i in model.V for j in model.V if i < j]
    arcs = [
        (tail, head)
        for i, j in edges
        for tail, head in ((i, j), (j, i))
    ]

    model.E = pyo.Set(dimen=2, initialize=edges)
    model.A = pyo.Set(dimen=2, initialize=arcs)
    model.link_cost = pyo.Param(
        model.E,
        initialize={(i, j): costs[i, j] for i, j in edges},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.E, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    # Connectivity together with exactly |V|-1 edges enforces a tree.
    model.tree_edge_count = pyo.Constraint(
        expr=sum(model.selected[i, j] for i, j in model.E)
        == model.branch_count - 1
    )

    def degree_rule(network, vertex):
        return sum(
            network.selected[min(vertex, other), max(vertex, other)]
            for other in network.V
            if other != vertex
        ) <= network.degree_limit

    model.degree_bounds = pyo.Constraint(model.V, rule=degree_rule)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= (
            (network.branch_count - 1)
            * network.selected[min(tail, head), max(tail, head)]
        )

    model.flow_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    def balance_rule(network, vertex):
        net_outflow = sum(
            network.flow[vertex, other] - network.flow[other, vertex]
            for other in network.V
            if other != vertex
        )
        required_outflow = network.branch_count - 1 if vertex == 1 else -1
        return net_outflow == required_outflow

    model.flow_balance = pyo.Constraint(model.V, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.link_cost[i, j] * model.selected[i, j]
            for i, j in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this error when it cannot load a feasible solution.
        # All other runtime errors propagate to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}