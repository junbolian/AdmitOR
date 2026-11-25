import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    coords = params["coords"]
    arcs = params["arcs"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    num_arcs = len(arcs)

    model = gp.Model("min_cost_cut")
    model.setParam("OutputFlag", 0)

    # x[i] = 0  =>  node i in S;  x[i] = 1  =>  node i in T
    x = model.addVars(num_nodes, vtype=GRB.BINARY, name="x")

    # y[k] = 1  =>  arc k crosses from S to T  (continuous suffices given binary x)
    y = model.addVars(num_arcs, lb=0, ub=1, vtype=GRB.CONTINUOUS, name="y")

    # Source must be in S, sink must be in T
    model.addConstr(x[source] == 0)
    model.addConstr(x[sink] == 1)

    # Link y and x so that y[k] = 1  iff  x[i]=0 and x[j]=1
    # Upper bounds prevent y=1 on non-crossing arcs (important if costs are negative)
    for k, (i, j) in enumerate(arcs):
        model.addConstr(y[k] >= x[j] - x[i])
        model.addConstr(y[k] <= 1 - x[i])
        model.addConstr(y[k] <= x[j])

    # Minimize total cut cost = sum of arc_unit_costs over arcs crossing S -> T
    model.setObjective(
        gp.quicksum(arc_unit_costs[k] * y[k] for k in range(num_arcs)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}