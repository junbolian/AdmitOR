# IR: {"sets":{"V":"{0,...,11}","D":"{0,1}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"coordinates[i,d]":"params['device_coordinates'][i][d] (survey metadata)","cost[i,j]":"params['distance_matrix'][i][j]","degree_limit":"params['max_degree']","root":"first vertex in V (structural)","capacity":"|V|-1 (structural)"},"variables":{"edge[i,j]":"Binary, (i,j) in E","flow[i,j]":"NonNegativeReals, (i,j) in A"},"constraints":["sum(edge[i,j] for (i,j) in E) = |V|-1","sum(edge[min(v,u),max(v,u)] for u in V if u!=v) <= degree_limit for each v in V","flow[i,j] <= capacity*edge[min(i,j),max(i,j)] for each (i,j) in A","sum(flow[v,u]-flow[u,v] for u in V if u!=v) = capacity if v=root else -1 for each v in V"],"objective":"minimize sum(cost[i,j]*edge[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    device_coordinates = params["device_coordinates"]
    distance_matrix = params["distance_matrix"]
    max_degree = params["max_degree"]

    vertices = tuple(range(12))
    dimensions = (0, 1)
    root = vertices[0]
    capacity = len(vertices) - 1
    edges = [(i, j) for i in vertices for j in vertices if i < j]
    arcs = [(i, j) for i in vertices for j in vertices if i != j]

    model = pyo.ConcreteModel()

    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.dimensions = pyo.Set(initialize=dimensions, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)

    model.coordinates = pyo.Param(
        model.vertices,
        model.dimensions,
        initialize={
            (i, d): device_coordinates[i][d]
            for i in vertices
            for d in dimensions
        },
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.edges,
        initialize={(i, j): distance_matrix[i][j] for i, j in edges},
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=max_degree,
        within=pyo.Reals,
    )

    model.edge = pyo.Var(model.edges, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.edge_count = pyo.Constraint(
        expr=sum(model.edge[i, j] for i, j in edges) == capacity
    )

    def degree_rule(network, vertex):
        return (
            sum(
                network.edge[min(vertex, neighbor), max(vertex, neighbor)]
                for neighbor in vertices
                if neighbor != vertex
            )
            <= network.degree_limit
        )

    model.degree_bounds = pyo.Constraint(model.vertices, rule=degree_rule)

    def flow_capacity_rule(network, i, j):
        return (
            network.flow[i, j]
            <= capacity * network.edge[min(i, j), max(i, j)]
        )

    model.flow_capacity = pyo.Constraint(
        model.arcs, rule=flow_capacity_rule
    )

    def flow_balance_rule(network, vertex):
        net_outflow = sum(
            network.flow[vertex, neighbor] - network.flow[neighbor, vertex]
            for neighbor in vertices
            if neighbor != vertex
        )
        required_outflow = capacity if vertex == root else -1
        return net_outflow == required_outflow

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=flow_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.edge[i, j]
            for i, j in edges
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}