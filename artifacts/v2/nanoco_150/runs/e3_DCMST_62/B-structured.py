# IR: {"sets":{"V":"{0,...,11}","D":"{0,1}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"coordinates_0":"surveyed coordinate pair","coordinates_1":"surveyed coordinate pair","coordinates_2":"surveyed coordinate pair","coordinates_3":"surveyed coordinate pair","coordinates_4":"surveyed coordinate pair","coordinates_5":"surveyed coordinate pair","coordinates_6":"surveyed coordinate pair","coordinates_7":"surveyed coordinate pair","coordinates_8":"surveyed coordinate pair","coordinates_9":"surveyed coordinate pair","coordinates_10":"surveyed coordinate pair","coordinates_11":"surveyed coordinate pair","distance_matrix":"direct wire costs on V x V","max_degree":"maximum incident selected edges per node"},"variables":{"x[E]":"binary; selected undirected edges","flow[A]":"nonnegative continuous; connectivity flow from root 0"},"constraints":["sum(x[i,j] for (i,j) in E) = |V|-1","sum(x[min(v,u),max(v,u)] for u in V if u!=v) <= max_degree for v in V","sum(flow[v,u]-flow[u,v] for u in V if u!=v) = (|V|-1 if v==0 else -1) for v in V","flow[i,j] <= (|V|-1)*x[min(i,j),max(i,j)] for (i,j) in A"],"objective":"minimize sum(distance_matrix[i,j]*x[i,j] for (i,j) in E)","metadata":"Surveyed coordinates are retained as parameters; supplied distances determine costs."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coordinates = [
        params["coordinates_0"],
        params["coordinates_1"],
        params["coordinates_2"],
        params["coordinates_3"],
        params["coordinates_4"],
        params["coordinates_5"],
        params["coordinates_6"],
        params["coordinates_7"],
        params["coordinates_8"],
        params["coordinates_9"],
        params["coordinates_10"],
        params["coordinates_11"],
    ]
    distance_matrix = params["distance_matrix"]
    max_degree = params["max_degree"]

    vertices = list(range(12))
    edges = [(i, j) for i in vertices for j in vertices if i < j]
    arcs = [(i, j) for i in vertices for j in vertices if i != j]
    required_edges = len(vertices) - 1

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vertices, ordered=True)
    model.D = pyo.Set(initialize=[0, 1], ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.surveyed_coordinates = pyo.Param(
        model.V,
        model.D,
        initialize=lambda mdl, i, dimension: coordinates[i][dimension],
        within=pyo.Reals,
    )
    model.wire_distance = pyo.Param(
        model.V,
        model.V,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=max_degree,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    model.edge_count_constraint = pyo.Constraint(
        expr=sum(model.x[i, j] for i, j in edges) == required_edges
    )

    def degree_rule(mdl, vertex):
        return (
            sum(
                mdl.x[min(vertex, other), max(vertex, other)]
                for other in vertices
                if other != vertex
            )
            <= mdl.degree_limit
        )

    model.degree_constraints = pyo.Constraint(model.V, rule=degree_rule)

    def flow_balance_rule(mdl, vertex):
        net_outflow = sum(
            mdl.flow[vertex, other] - mdl.flow[other, vertex]
            for other in vertices
            if other != vertex
        )
        return net_outflow == (required_edges if vertex == 0 else -1)

    model.flow_balance_constraints = pyo.Constraint(
        model.V, rule=flow_balance_rule
    )

    def flow_capacity_rule(mdl, i, j):
        return (
            mdl.flow[i, j]
            <= required_edges * mdl.x[min(i, j), max(i, j)]
        )

    model.flow_capacity_constraints = pyo.Constraint(
        model.A, rule=flow_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.wire_distance[i, j] * model.x[i, j]
            for i, j in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when it cannot load a solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}