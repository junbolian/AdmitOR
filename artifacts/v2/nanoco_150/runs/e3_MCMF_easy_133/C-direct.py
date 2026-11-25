import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]

    # Arc definitions: (from, to)
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7)
    ]
    assert len(arcs) == 17
    assert len(arc_capacity) == 17
    assert len(arc_cost) == 17

    cap = {arcs[i]: arc_capacity[i] for i in range(17)}
    cost = {arcs[i]: arc_cost[i] for i in range(17)}

    nodes = list(range(8))
    source = 0
    sink = 7

    # Phase 1: Maximize flow
    model = gp.Model("maxflow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow conservation for intermediate nodes
    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == nd)
        out_flow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == nd)
        model.addConstr(in_flow == out_flow, name=f"conserve_{nd}")

    # Total flow out of source
    total_flow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == source)

    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_flow_value = model.ObjVal

    # Phase 2: Minimize cost subject to achieving max flow
    model2 = gp.Model("mincost")
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(arcs, lb=0.0, name="flow2")

    for arc in arcs:
        model2.addConstr(flow2[arc] <= cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow2 = gp.quicksum(flow2[arc] for arc in arcs if arc[1] == nd)
        out_flow2 = gp.quicksum(flow2[arc] for arc in arcs if arc[0] == nd)
        model2.addConstr(in_flow2 == out_flow2, name=f"conserve_{nd}")

    total_flow2 = gp.quicksum(flow2[arc] for arc in arcs if arc[0] == source)
    model2.addConstr(total_flow2 == max_flow_value, name="fix_flow")

    total_cost = gp.quicksum(cost[arc] * flow2[arc] for arc in arcs)
    model2.setObjective(total_cost, GRB.MINIMIZE)
    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    return {"objective": model2.ObjVal, "status": "optimal"}