# IR: {"sets":{"N":["S","2","3","4","5","6","7","T"],"A":[["S","2"],["S","3"],["2","S"],["2","4"],["2","3"],["3","S"],["3","2"],["3","5"],["3","6"],["4","2"],["4","6"],["5","3"],["5","T"],["6","3"],["6","4"],["6","7"],["7","6"],["7","T"],["T","5"],["T","7"]]},"params":{"w[i,j]":{"source":"params['w_'+i+'_'+j]","domain":"NonNegativeReals","index":"A"}},"variables":{"x[i,j]":{"type":"Binary","index":"A"}},"constraints":["For each v in N: sum(x[v,j] for outgoing arcs) - sum(x[i,v] for incoming arcs) = 1 if v=S, -1 if v=T, otherwise 0."],"objective":{"sense":"minimize","expression":"sum(w[i,j]*x[i,j] for (i,j) in A)"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ["S", "2", "3", "4", "5", "6", "7", "T"]

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

    outgoing = {
        node: [arc for arc in weights if arc[0] == node]
        for node in nodes
    }
    incoming = {
        node: [arc for arc in weights if arc[1] == node]
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=list(weights), ordered=True)
    model.distance = pyo.Param(
        model.arcs,
        initialize=weights,
        within=pyo.NonNegativeReals,
    )
    model.arc_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(instance, node):
        supply = 1 if node == "S" else (-1 if node == "T" else 0)
        return (
            sum(instance.arc_used[arc] for arc in outgoing[node])
            - sum(instance.arc_used[arc] for arc in incoming[node])
            == supply
        )

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )
    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[tail, head] * model.arc_used[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}