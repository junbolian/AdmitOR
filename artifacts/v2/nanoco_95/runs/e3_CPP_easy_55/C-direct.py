import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_cost = {
        (0,1): params["edge_cost_0_1"],
        (0,2): params["edge_cost_0_2"],
        (1,3): params["edge_cost_1_3"],
        (2,6): params["edge_cost_2_6"],
        (3,4): params["edge_cost_3_4"],
        (3,5): params["edge_cost_3_5"],
        (3,6): params["edge_cost_3_6"],
        (5,6): params["edge_cost_5_6"],
    }

    # Deadhead cost matrix (symmetric): d[i][j]
    n = 7
    nodes = list(range(n))

    dh_keys = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
        (1,2),(1,3),(1,4),(1,5),(1,6),
        (2,3),(2,4),(2,5),(2,6),
        (3,4),(3,5),(3,6),
        (4,5),(4,6),
        (5,6),
    ]

    dh_raw = {}
    for (i,j) in dh_keys:
        key = f"deadhead_cost_{i}_{j}"
        dh_raw[(i,j)] = params[key]
        dh_raw[(j,i)] = params[key]
    for i in nodes:
        dh_raw[(i,i)] = 0.0

    garage = int(params["garage_node"])

    # Required edges (undirected). We model each required edge (i,j) as two
    # directed traversal variables: x[i,j] = times traversed i->j for service,
    #                                        x[j,i] = times traversed j->i for service.
    # Additionally, deadhead arcs y[i,j] for all ordered pairs.
    #
    # For a required edge (i,j), service cost is edge_cost[(i,j)] per traversal
    # (either direction counts as servicing it once more).
    # Deadhead arcs carry deadhead cost.
    #
    # Constraints:
    #   - Each required edge must be traversed (service) at least once total
    #     across both directions: x[i,j] + x[j,i] >= 1
    #   - Flow conservation at every node (excluding garage):
    #     sum of all outgoing arcs = sum of all incoming arcs
    #   - At garage: net outflow = 0 (tour returns)
    #   - All variables >= 0, integer.

    required_edges = list(edge_cost.keys())

    # Directed service arcs: for each required undirected edge, two directions
    service_arcs = []
    for (i,j) in required_edges:
        service_arcs.append((i,j))
        service_arcs.append((j,i))

    # Deadhead arcs: all ordered pairs (i,j) with i != j
    deadhead_arcs = [(i,j) for i in nodes for j in nodes if i != j]

    model = gp.Model("route_inspection")
    model.setParam("OutputFlag", 0)

    # Service traversal variables (integer, >= 0)
    x = model.addVars(service_arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Deadhead traversal variables (integer, >= 0)
    y = model.addVars(deadhead_arcs, vtype=GRB.INTEGER, lb=0, name="y")

    # Objective: sum of service costs + deadhead costs
    obj = gp.LinExpr()
    for (i,j) in required_edges:
        c = edge_cost[(i,j)]
        obj += c * x[i,j] + c * x[j,i]
    for (i,j) in deadhead_arcs:
        obj += dh_raw[(i,j)] * y[i,j]

    model.setObjective(obj, GRB.MINIMIZE)

    # Each required edge must be serviced at least once (sum of both directions >= 1)
    for (i,j) in required_edges:
        model.addConstr(x[i,j] + x[j,i] >= 1, name=f"service_{i}_{j}")

    # Flow conservation at every node
    # Total outflow = total inflow for all nodes (closed tour)
    for v in nodes:
        outflow = gp.LinExpr()
        inflow = gp.LinExpr()

        # Service arcs
        for (i,j) in service_arcs:
            if i == v:
                outflow += x[i,j]
            if j == v:
                inflow += x[i,j]

        # Deadhead arcs
        for (i,j) in deadhead_arcs:
            if i == v:
                outflow += y[i,j]
            if j == v:
                inflow += y[i,j]

        model.addConstr(outflow == inflow, name=f"flow_{v}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}