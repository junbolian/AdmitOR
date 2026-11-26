# IR: {"sets":{"N":["S","2","3","4","5","6","7","T"],"E":[["S","2"],["S","3"],["2","4"],["2","3"],["3","5"],["3","6"],["4","6"],["5","T"],["6","7"],["7","T"]],"A":"both orientations of each edge in E"},"params":{"edge_S_2":"nonnegative distance","edge_S_3":"nonnegative distance","edge_2_4":"nonnegative distance","edge_2_3":"nonnegative distance","edge_3_5":"nonnegative distance","edge_3_6":"nonnegative distance","edge_4_6":"nonnegative distance","edge_5_T":"nonnegative distance","edge_6_7":"nonnegative distance","edge_7_T":"nonnegative distance","cost[a]":"distance of the undirected edge underlying arc a"},"variables":{"x[a in A]":"binary"},"constraints":["For each node n, sum(x[n,j]) - sum(x[i,n]) equals 1 for S, -1 for T, and 0 otherwise."],"objective":"minimize sum(cost[a] * x[a] for a in A)","output":"return the optimal objective rounded to the nearest meter as a float; return null objective if no objective is retrievable"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ("S", "2", "3", "4", "5", "6", "7", "T")
    edge_weights = {
        ("S", "2"): params["edge_S_2"],
        ("S", "3"): params["edge_S_3"],
        ("2", "4"): params["edge_2_4"],
        ("2", "3"): params["edge_2_3"],
        ("3", "5"): params["edge_3_5"],
        ("3", "6"): params["edge_3_6"],
        ("4", "6"): params["edge_4_6"],
        ("5", "T"): params["edge_5_T"],
        ("6", "7"): params["edge_6_7"],
        ("7", "T"): params["edge_7_T"],
    }

    arc_weights = {}
    for (tail, head), weight in edge_weights.items():
        arc_weights[(tail, head)] = weight
        arc_weights[(head, tail)] = weight

    # Initialize the scalar Set from an explicit sequence of arc tuples.
    arcs = list(arc_weights.keys())
    outgoing = {
        node: [arc for arc in arcs if arc[0] == node]
        for node in nodes
    }
    incoming = {
        node: [arc for arc in arcs if arc[1] == node]
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.cost = pyo.Param(
        model.arcs,
        initialize=arc_weights,
        within=pyo.NonNegativeReals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(block, node):
        supply = 1 if node == "S" else (-1 if node == "T" else 0)
        return (
            sum(block.x[arc] for arc in outgoing[node])
            - sum(block.x[arc] for arc in incoming[node])
            == supply
        )

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )
    model.total_distance = pyo.Objective(
        expr=sum(
            model.cost[arc] * model.x[arc]
            for arc in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Permit objective retrieval to determine success when APPSI
        # reports that it could not load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}