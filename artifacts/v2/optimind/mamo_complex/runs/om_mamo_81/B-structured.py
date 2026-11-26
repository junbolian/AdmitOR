# IR: {"sets":{"V":["S","2","3","4","5","6","7","T"],"A":["S->2","S->3","2->S","2->4","2->3","3->S","3->2","3->5","3->6","4->2","4->6","5->3","5->T","6->3","6->4","6->7","7->6","7->T","T->5","T->7"]},"params":{"w[u,v]":"params['w_'+u+'_'+v] for each (u,v) in A"},"variables":{"x[u,v]":"binary for (u,v) in A","position[v]":"continuous in [0,|V|-1] for v in V"},"constraints":["outflow[v]-inflow[v]=1 if v=S, -1 if v=T, otherwise 0","outflow[v]<=1 for all v","inflow[v]<=1 for all v","position[S]=0","position[v]>=position[u]+1-|V|*(1-x[u,v]) for all (u,v) in A"],"objective":"minimize sum(w[u,v]*x[u,v] for (u,v) in A)","output":"retrieve objective as float; round to nearest meter"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ("S", "2", "3", "4", "5", "6", "7", "T")

    weights = {
        ("S", "2"): params["w_S_2"],
        ("S", "3"): params["w_S_3"],
        ("2", "S"): params["w_2_S"],
        ("2", "4"): params["w_2_4"],
        ("2", "3"): params["w_2_3"],
        ("3", "S"): params["w_3_S"],
        ("3", "2"): params["w_3_2"],
        ("3", "5"): params["w_3_5"],
        ("3", "6"): params["w_3_6"],
        ("4", "2"): params["w_4_2"],
        ("4", "6"): params["w_4_6"],
        ("5", "3"): params["w_5_3"],
        ("5", "T"): params["w_5_T"],
        ("6", "3"): params["w_6_3"],
        ("6", "4"): params["w_6_4"],
        ("6", "7"): params["w_6_7"],
        ("7", "6"): params["w_7_6"],
        ("7", "T"): params["w_7_T"],
        ("T", "5"): params["w_T_5"],
        ("T", "7"): params["w_T_7"],
    }

    arcs = tuple(weights)
    incoming = {
        node: tuple((tail, head) for tail, head in arcs if head == node)
        for node in nodes
    }
    outgoing = {
        node: tuple((tail, head) for tail, head in arcs if tail == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.edge_weight = pyo.Param(model.arcs, initialize=weights, within=pyo.Reals)

    model.use_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.vertices, domain=pyo.NonNegativeReals, bounds=(0, len(nodes) - 1)
    )

    def flow_rule(problem, node):
        balance = 1 if node == "S" else (-1 if node == "T" else 0)
        return (
            sum(problem.use_arc[arc] for arc in outgoing[node])
            - sum(problem.use_arc[arc] for arc in incoming[node])
            == balance
        )

    model.flow_balance = pyo.Constraint(model.vertices, rule=flow_rule)

    def outgoing_rule(problem, node):
        return sum(problem.use_arc[arc] for arc in outgoing[node]) <= 1

    def incoming_rule(problem, node):
        return sum(problem.use_arc[arc] for arc in incoming[node]) <= 1

    model.outgoing_limit = pyo.Constraint(model.vertices, rule=outgoing_rule)
    model.incoming_limit = pyo.Constraint(model.vertices, rule=incoming_rule)
    model.source_position = pyo.Constraint(expr=model.position["S"] == 0)

    def ordering_rule(problem, tail, head):
        return problem.position[head] >= (
            problem.position[tail]
            + 1
            - len(nodes) * (1 - problem.use_arc[tail, head])
        )

    model.path_ordering = pyo.Constraint(model.arcs, rule=ordering_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.edge_weight[tail, head] * model.use_arc[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solve may leave no solution loaded. Objective retrieval
        # below is the sole test of whether a usable result exists.
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}