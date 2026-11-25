# IR: {"sets":{"N":[0,1,2,3,4,5],"E":[[0,3],[0,4],[1,4],[2,3],[2,5],[3,4],[4,5]],"A":"both orientations of E; travel is restricted to these seven streets"},"params":{"service_cost":"params['service_cost'][k], indexed by E in listed order","travel_cost":"params['travel_cost'], accepted as a flat row-major sequence or a nested 6x6 matrix"},"variables":{"service[i,j]":"nonnegative integer for (i,j) in A","deadhead[i,j]":"nonnegative integer for (i,j) in A"},"constraints":{"required_service":"service[i,j]+service[j,i]>=1 for each (i,j) in E","flow_balance":"sum outgoing(service+deadhead)=sum incoming(service+deadhead) at each node"},"objective":"minimize sum over A of service_cost[min(i,j),max(i,j)]*service[i,j]+travel_cost[i,j]*deadhead[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    service_values = params["service_cost"]
    travel_values = params["travel_cost"]

    nodes = tuple(range(6))
    node_count = len(nodes)
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
        directed_arc
        for first, second in edges
        for directed_arc in ((first, second), (second, first))
    )

    if len(service_values) != len(edges):
        return {"objective": None, "status": "invalid_service_cost"}

    if len(travel_values) == node_count:
        if any(
            not hasattr(row, "__len__") or len(row) != node_count
            for row in travel_values
        ):
            return {"objective": None, "status": "invalid_travel_cost"}

        travel_data = {
            (first, second): travel_values[first][second]
            for first in nodes
            for second in nodes
        }
    elif len(travel_values) == node_count * node_count:
        travel_data = {
            (first, second): travel_values[node_count * first + second]
            for first in nodes
            for second in nodes
        }
    else:
        return {"objective": None, "status": "invalid_travel_cost"}

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.service_cost = pyo.Param(
        model.E,
        initialize={
            edge: service_values[position]
            for position, edge in enumerate(edges)
        },
        within=pyo.Reals,
    )
    model.travel_cost = pyo.Param(
        model.N,
        model.N,
        initialize=travel_data,
        within=pyo.Reals,
    )

    model.service = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.deadhead = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)

    def required_service_rule(mdl, first, second):
        return mdl.service[first, second] + mdl.service[second, first] >= 1

    model.required_service = pyo.Constraint(
        model.E, rule=required_service_rule
    )

    def flow_balance_rule(mdl, node):
        outgoing = sum(
            mdl.service[first, second] + mdl.deadhead[first, second]
            for first, second in arcs
            if first == node
        )
        incoming = sum(
            mdl.service[first, second] + mdl.deadhead[first, second]
            for first, second in arcs
            if second == node
        )
        return outgoing == incoming

    model.flow_balance = pyo.Constraint(model.N, rule=flow_balance_rule)

    # All required edges together form a connected spanning graph containing
    # depot 0. Required service and integer flow balance therefore guarantee
    # an Euler circuit that can begin and end at depot 0.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.service_cost[min(first, second), max(first, second)]
            * model.service[first, second]
            + model.travel_cost[first, second]
            * model.deadhead[first, second]
            for first, second in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}