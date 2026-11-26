import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    bw_A_B = params["bw_A_B"]
    bw_A_C = params["bw_A_C"]
    bw_A_E = params["bw_A_E"]
    bw_B_A = params["bw_B_A"]
    bw_B_C = params["bw_B_C"]
    bw_B_D = params["bw_B_D"]
    bw_B_E = params["bw_B_E"]
    bw_C_A = params["bw_C_A"]
    bw_C_D = params["bw_C_D"]
    bw_C_E = params["bw_C_E"]
    bw_D_A = params["bw_D_A"]
    bw_D_B = params["bw_D_B"]
    bw_D_C = params["bw_D_C"]
    bw_D_E = params["bw_D_E"]
    bw_E_B = params["bw_E_B"]
    bw_E_D = params["bw_E_D"]
    zero_bandwidth = params["zero_bandwidth"]

    nodes = ["A", "B", "C", "D", "E"]

    # Provided bandwidths; missing entries default to zero_bandwidth.
    bw_given = {
        ("A", "B"): bw_A_B,
        ("A", "C"): bw_A_C,
        ("A", "E"): bw_A_E,
        ("B", "A"): bw_B_A,
        ("B", "C"): bw_B_C,
        ("B", "D"): bw_B_D,
        ("B", "E"): bw_B_E,
        ("C", "A"): bw_C_A,
        ("C", "D"): bw_C_D,
        ("C", "E"): bw_C_E,
        ("D", "A"): bw_D_A,
        ("D", "B"): bw_D_B,
        ("D", "C"): bw_D_C,
        ("D", "E"): bw_D_E,
        ("E", "B"): bw_E_B,
        ("E", "D"): bw_E_D,
    }

    bw = {}
    for u in nodes:
        for v in nodes:
            if u == v:
                continue
            bw[(u, v)] = bw_given.get((u, v), zero_bandwidth)

    arcs = [(u, v) for u in nodes for v in nodes if u != v]
    usable_arcs = [a for a in arcs if bw[a] > zero_bandwidth]

    model = pyo.ConcreteModel()
    model.NODES = pyo.Set(initialize=nodes)
    model.USABLE = pyo.Set(initialize=usable_arcs, dimen=2)

    model.flow = pyo.Var(model.USABLE, domain=pyo.Binary)
    model.bottleneck = pyo.Var(within=pyo.NonNegativeReals)

    def balance_rule(model, n):
        outflow = sum(model.flow[(u, v)] for (u, v) in model.USABLE if u == n)
        inflow = sum(model.flow[(u, v)] for (u, v) in model.USABLE if v == n)
        if n == "A":
            return inflow - outflow == -1
        elif n == "E":
            return inflow - outflow == 1
        return inflow - outflow == 0

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    # Path must pass through C: exactly one arc enters C and one leaves C.
    model.visit_C_in = pyo.Constraint(
        expr=sum(model.flow[(u, "C")] for (u, v) in model.USABLE if v == "C") == 1
    )
    model.visit_C_out = pyo.Constraint(
        expr=sum(model.flow[("C", v)] for (u, v) in model.USABLE if u == "C") == 1
    )

    # Forbid using an arc and its reverse simultaneously.
    def no_two_cycle_rule(model, u, v):
        if (v, u) in [(a, b) for (a, b) in model.USABLE]:
            return model.flow[(u, v)] + model.flow[(v, u)] <= 1
        return pyo.Constraint.Skip

    model.no_two_cycle = pyo.Constraint(model.USABLE, rule=no_two_cycle_rule)

    bigM = sum(bw[a] for a in usable_arcs) + 1

    def bottleneck_rule(model, u, v):
        return model.bottleneck <= bw[(u, v)] + bigM * (1 - model.flow[(u, v)])

    model.bottleneck_con = pyo.Constraint(model.USABLE, rule=bottleneck_rule)

    model.OBJ = pyo.Objective(expr=model.bottleneck, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.OBJ))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}