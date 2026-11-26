# IR: {"sets":{"N":["S","2","3","4","5","6","7","T"],"A":[["S","2"],["S","3"],["2","S"],["2","4"],["2","3"],["3","S"],["3","2"],["3","5"],["3","6"],["4","2"],["4","6"],["5","3"],["5","T"],["6","3"],["6","4"],["6","7"],["7","6"],["7","T"],["T","5"],["T","7"]]},"params":{"distance[i,j]":{"source":"params['edge_'+i+'_'+j]","domain":"nonnegative real"}},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each v in N: sum(x[v,j]) - sum(x[i,v]) = 1 if v=S, -1 if v=T, else 0."],"objective":"Minimize sum(distance[i,j]*x[i,j] for (i,j) in A); report the objective rounded to the nearest meter."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = {
        ("S", "2"): params["edge_S_2"],
        ("S", "3"): params["edge_S_3"],
        ("2", "S"): params["edge_2_S"],
        ("2", "4"): params["edge_2_4"],
        ("2", "3"): params["edge_2_3"],
        ("3", "S"): params["edge_3_S"],
        ("3", "2"): params["edge_3_2"],
        ("3", "5"): params["edge_3_5"],
        ("3", "6"): params["edge_3_6"],
        ("4", "2"): params["edge_4_2"],
        ("4", "6"): params["edge_4_6"],
        ("5", "3"): params["edge_5_3"],
        ("5", "T"): params["edge_5_T"],
        ("6", "3"): params["edge_6_3"],
        ("6", "4"): params["edge_6_4"],
        ("6", "7"): params["edge_6_7"],
        ("7", "6"): params["edge_7_6"],
        ("7", "T"): params["edge_7_T"],
        ("T", "5"): params["edge_T_5"],
        ("T", "7"): params["edge_T_7"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(
        initialize=["S", "2", "3", "4", "5", "6", "7", "T"],
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=list(distances),
        ordered=True,
    )
    model.distance = pyo.Param(
        model.arcs,
        initialize=distances,
        within=pyo.NonNegativeReals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(instance, node):
        outgoing = sum(
            instance.x[tail, head]
            for tail, head in instance.arcs
            if tail == node
        )
        incoming = sum(
            instance.x[tail, head]
            for tail, head in instance.arcs
            if head == node
        )
        supply = 1 if node == "S" else -1 if node == "T" else 0
        return outgoing - incoming == supply

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )
    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[tail, head] * model.x[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}