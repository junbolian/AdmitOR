import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Capacity parameters
    cap_0_1 = params["capacity_0_1"]
    cap_0_2 = params["capacity_0_2"]
    cap_0_3 = params["capacity_0_3"]
    cap_0_4 = params["capacity_0_4"]
    cap_0_5 = params["capacity_0_5"]
    cap_0_6 = params["capacity_0_6"]
    cap_0_7 = params["capacity_0_7"]
    cap_0_8 = params["capacity_0_8"]
    cap_2_1_5_high = params["capacity_1_5_high"]
    cap_low = params["capacity_range_low"]
    cap_high = params["capacity_range_high"]

    N = 9

    # Build edge capacity dictionary
    # Edges from source 0
    edge_cap = {}
    edge_cap[(0, 1)] = cap_0_1
    edge_cap[(0, 2)] = cap_0_2
    edge_cap[(0, 3)] = cap_0_3
    edge_cap[(0, 4)] = cap_0_4
    edge_cap[(0, 5)] = cap_0_5
    edge_cap[(0, 6)] = cap_0_6
    edge_cap[(0, 7)] = cap_0_7
    edge_cap[(0, 8)] = cap_0_8

    # Edges among centers 1..8 (to higher-numbered centers)
    for i in range(1, N):
        for j in range(i + 1, N):
            if (i == 2 and j in (1, 5)) or (j == 2 and i in (1, 5)):
                edge_cap[(i, j)] = cap_2_1_5_high
            elif (i, j) == (2, 1) or (i, j) == (2, 5):
                edge_cap[(i, j)] = cap_2_1_5_high
            elif i == 2 and j == 1:
                edge_cap[(i, j)] = cap_2_1_5_high
            else:
                edge_cap[(i, j)] = cap_high

    # Handle special edges: center 2 to 1 and 5 are high capacity
    # (2->1 and 2->5 are explicitly described as high 18)
    edge_cap[(1, 2)] = cap_2_1_5_high
    edge_cap[(2, 5)] = cap_2_1_5_high
    # Feedback edges from sink 8 back into network (low capacity)
    for k in range(1, 8):
        edge_cap[(8, k)] = cap_low

    edges = list(edge_cap.keys())

    model = pyo.ConcreteModel()
    model.NODES = pyo.RangeSet(0, N - 1)
    model.EDGES = pyo.Set(initialize=edges, dimen=2)

    model.flow = pyo.Var(model.EDGES, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= edge_cap[(i, j)]

    model.cap_con = pyo.Constraint(model.EDGES, rule=cap_rule)

    # Flow conservation: source has net outflow = F, sink net inflow = F,
    # intermediate nodes balanced.
    model.F = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(mdl, n):
        inflow = 0
        outflow = 0
        for (i, j) in edges:
            if j == n:
                inflow = inflow + mdl.flow[i, j]
            if i == n:
                outflow = outflow + mdl.flow[i, j]
        if n == 0:
            return outflow - inflow == mdl.F
        elif n == N - 1:
            return inflow - outflow == mdl.F
        else:
            return inflow - outflow == 0

    model.balance_con = pyo.Constraint(model.NODES, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.F, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}