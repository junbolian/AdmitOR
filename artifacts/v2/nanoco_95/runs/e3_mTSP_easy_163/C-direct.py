import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coords = params["node_coordinates"]
    dist = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    num_clinics = params["num_clinic_nodes"]

    n = num_clinics + 1  # total nodes: depot + clinics
    nodes = list(range(n))
    clinics = list(range(1, n))  # clinic node indices (depot is 0)

    model = gp.Model("vrp")
    model.Params.OutputFlag = 0

    # x[i,j] = 1 if some vehicle traverses arc i -> j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # MTZ position variables for clinics (used to eliminate subtours among clinics)
    u = {}
    for i in clinics:
        u[i] = model.addVar(lb=1, ub=num_clinics, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE,
    )

    # Each clinic is entered exactly once
    for j in clinics:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1)

    # Each clinic is left exactly once
    for i in clinics:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if i != j) == 1)

    # All vehicles depart from and return to the depot
    model.addConstr(gp.quicksum(x[0, j] for j in clinics) == num_vehicles)
    model.addConstr(gp.quicksum(x[i, 0] for i in clinics) == num_vehicles)

    # MTZ subtour-elimination: along any used clinic-to-clinic arc, positions strictly increase
    for i in clinics:
        for j in clinics:
            if i != j:
                model.addConstr(u[i] - u[j] + num_clinics * x[i, j] <= num_clinics - 1)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}