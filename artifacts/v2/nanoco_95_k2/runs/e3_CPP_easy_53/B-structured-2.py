# IR: {"sets":{"V":[0,1,2,3,4,5],"E":[[0,3],[0,4],[1,4],[2,3],[2,5],[3,4],[4,5]],"A":"both orientations of E"},"params":{"service_cost":"7 costs in E order, read from params","travel_cost":"6x6 nested matrix or 36 row-major costs, read from params"},"variables":{"service[i,j]":"nonnegative integer on A","deadhead[i,j]":"nonnegative integer on A"},"constraints":["For every (u,v) in E: service[u,v]+service[v,u]>=1.","For every v in V: incoming service and deadhead traversals equal outgoing service and deadhead traversals."],"objective":"Minimize sum over A of service_cost[edge(i,j)]*service[i,j]+travel_cost[i,j]*deadhead[i,j].","connectivity":"All required edges form a connected spanning graph containing depot 0; coverage and balance guarantee a single closed Euler route through depot 0."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    edges = (
        (0, 3),
        (0, 4),
        (1, 4),
        (2, 3),
        (2, 5),
        (3, 4),
        (4, 5),
    )
    arcs = tuple(
        arc
        for first, second in edges
        for arc in ((first, second), (second, first))
    )
    node_count = len(nodes)

    service_values = tuple(float(value) for value in params["service_cost"])
    if len(service_values) != len(edges):
        raise ValueError(
            "service_cost must contain 7 entries in the stated edge order."
        )

    raw_travel = params["travel_cost"]

    # Accept both a nested 6x6 matrix and a flat row-major sequence.
    if len(raw_travel) == node_count:
        if not all(isinstance(row, (list, tuple)) for row in raw_travel):
            raise ValueError(
                "travel_cost must be a 6x6 matrix or 36 row-major entries."
            )
        if any(len(row) != node_count for row in raw_travel):
            raise ValueError("Each travel_cost row must contain 6 entries.")
        travel_matrix = tuple(
            tuple(float(value) for value in row)
            for row in raw_travel
        )
    elif len(raw_travel) == node_count * node_count:
        travel_values = tuple(float(value) for value in raw_travel)
        travel_matrix = tuple(
            tuple(
                travel_values[node_count * first + second]
                for second in nodes
            )
            for first in nodes
        )
    else:
        raise ValueError(
            "travel_cost must be a 6x6 matrix or 36 row-major entries."
        )

    service_by_edge = dict(zip(edges, service_values))
    service_by_arc = {
        (first, second): service_by_edge[
            (min(first, second), max(first, second))
        ]
        for first, second in arcs
    }

    # Travel is restricted to the seven specified street segments.
    travel_by_arc = {
        (first, second): travel_matrix[first][second]
        for first, second in arcs
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }
    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.required_edges = pyo.Set(
        dimen=2, initialize=edges, ordered=True
    )
    model.directed_arcs = pyo.Set(
        dimen=2, initialize=arcs, ordered=True
    )

    model.service_rates = pyo.Param(
        model.directed_arcs, initialize=service_by_arc
    )
    model.travel_rates = pyo.Param(
        model.directed_arcs, initialize=travel_by_arc
    )

    model.service = pyo.Var(
        model.directed_arcs, domain=pyo.NonNegativeIntegers
    )
    model.deadhead = pyo.Var(
        model.directed_arcs, domain=pyo.NonNegativeIntegers
    )

    def coverage_rule(instance, first, second):
        return (
            instance.service[first, second]
            + instance.service[second, first]
            >= 1
        )

    model.service_coverage = pyo.Constraint(
        model.required_edges, rule=coverage_rule
    )

    def balance_rule(instance, node):
        return sum(
            instance.service[first, second]
            + instance.deadhead[first, second]
            for first, second in incoming[node]
        ) == sum(
            instance.service[first, second]
            + instance.deadhead[first, second]
            for first, second in outgoing[node]
        )

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.service_rates[first, second]
            * model.service[first, second]
            + model.travel_rates[first, second]
            * model.deadhead[first, second]
            for first, second in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Allow objective retrieval to determine success when Appsi cannot
        # load a feasible solution; propagate unexpected solver errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}