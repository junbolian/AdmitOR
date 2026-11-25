# {
#   "sets": {"N": "0..7", "K": [0, 1], "E": [[0,1],[0,3],[0,5],[0,6],[0,7],[1,2],[1,5],[1,6],[2,3],[2,6],[3,4],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]], "A": "For each (i,j) in E, append (i,j), then (j,i), preserving E order"},
#   "params": {"capacity[i,j]": "params['arc_capacities'][position of (i,j) in A]", "cost[i,j]": "params['arc_unit_costs'][position of (i,j) in A]", "demand[k]": "params['demands'][k]", "source": [3,1], "sink": [7,5]},
#   "variables": {"flow[k,i,j]": "nonnegative real, k in K, (i,j) in A"},
#   "constraints": ["For each k,n: sum(flow[k,n,j] over outgoing arcs) - sum(flow[k,i,n] over incoming arcs) = demand[k] if n=source[k], -demand[k] if n=sink[k], else 0", "For each (i,j): sum(flow[k,i,j] over k) <= capacity[i,j]"],
#   "objective": "minimize sum(cost[i,j] * flow[k,i,j] over k in K and (i,j) in A)"
# }

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    undirected_edges = [
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 5), (1, 6),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    arcs = [
        directed_arc
        for i, j in undirected_edges
        for directed_arc in ((i, j), (j, i))
    ]
    sources = (3, 1)
    sinks = (7, 5)

    capacities = params["arc_capacities"]
    costs = params["arc_unit_costs"]
    demands = params["demands"]

    if len(capacities) != len(arcs):
        return {"objective": None, "status": "invalid_capacities_length"}
    if len(costs) != len(arcs):
        return {"objective": None, "status": "invalid_costs_length"}
    if len(demands) != len(sources):
        return {"objective": None, "status": "invalid_demands_length"}

    outgoing = {
        node: [j for i, j in arcs if i == node]
        for node in range(8)
    }
    incoming = {
        node: [i for i, j in arcs if j == node]
        for node in range(8)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.commodities = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.commodities,
        initialize={k: demands[k] for k in range(2)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def balance_rule(grid, k, node):
        if node == sources[k]:
            net_supply = grid.demand[k]
        elif node == sinks[k]:
            net_supply = -grid.demand[k]
        else:
            net_supply = 0

        return (
            sum(grid.flow[k, node, j] for j in outgoing[node])
            - sum(grid.flow[k, i, node] for i in incoming[node])
            == net_supply
        )

    model.flow_balance = pyo.Constraint(
        model.commodities,
        model.nodes,
        rule=balance_rule,
    )

    def capacity_rule(grid, i, j):
        return (
            sum(grid.flow[k, i, j] for k in grid.commodities)
            <= grid.capacity[i, j]
        )

    model.shared_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.flow[k, i, j]
            for k in model.commodities
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_unavailable"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}