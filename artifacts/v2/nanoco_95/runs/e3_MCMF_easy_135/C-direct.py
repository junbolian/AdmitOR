import gurobipy as gp
from gurobipy import GRB


def solve(params):
    arcs = [(0, 1), (0, 2), (0, 6), (0, 8),
            (1, 2), (1, 5),
            (2, 3), (2, 6),
            (3, 4),
            (4, 5),
            (5, 6),
            (6, 7), (6, 8),
            (7, 8)]

    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]
    capacities = {a: params[f"capacity_{a[0]}_{a[1]}"] for a in arcs}
    costs = {a: params[f"cost_{a[0]}_{a[1]}"] for a in arcs}

    source = 0
    sink = 8
    nodes = list(range(num_nodes))

    out_arcs = {n: [] for n in nodes}
    in_arcs = {n: [] for n in nodes}
    for a in arcs:
        out_arcs[a[0]].append(a)
        in_arcs[a[1]].append(a)

    model = gp.Model("lex_flow")
    model.Params.OutputFlag = 0

    f = model.addVars(arcs, lb=0.0, ub=[capacities[a] for a in arcs], name="f")
    F = model.addVar(lb=0.0, name="F")

    for n in nodes:
        outflow = gp.quicksum(f[a] for a in out_arcs[n])
        inflow = gp.quicksum(f[a] for a in in_arcs[n])
        if n == source:
            model.addConstr(outflow - inflow == F, name=f"flow_src_{n}")
        elif n == sink:
            model.addConstr(inflow - outflow == F, name=f"flow_sink_{n}")
        else:
            model.addConstr(outflow - inflow == 0, name=f"flow_bal_{n}")

    model.setObjective(F, GRB.MAXIMIZE)
    model.optimize()

    if model.status != GRB.OPTIMAL:
        return {"objective": None, "status": "phase1_failed"}

    F_star = F.X

    model.addConstr(F == F_star, name="fix_throughput")
    model.setObjective(gp.quicksum(costs[a] * f[a] for a in arcs), GRB.MINIMIZE)
    model.optimize()

    if model.status != GRB.OPTIMAL:
        return {"objective": None, "status": "phase2_failed"}

    return {"objective": float(model.ObjVal), "status": "optimal"}