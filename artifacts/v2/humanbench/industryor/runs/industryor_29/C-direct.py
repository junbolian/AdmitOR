import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    supply = params["supply"]       # list of 6 values
    demand = params["demand"]       # list of 5 values
    cost_rate = params["cost_rate"] # euros per km per container
    distance = params["distance"]   # 6x5 matrix
    truck_capacity = params["truck_capacity"]  # max containers per truck

    warehouses = range(6)
    ports = range(5)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = number of containers shipped from warehouse i to port j
    x = model.addVars(warehouses, ports, vtype=GRB.INTEGER, lb=0, name="x")

    # Number of trucks needed for each route (ceiling of containers / truck_capacity)
    # Cost = cost_rate * distance[i][j] * x[i,j]
    # (cost per container proportional to distance, so total cost = cost_rate * dist * containers)
    obj = gp.quicksum(
        cost_rate * distance[i][j] * x[i, j]
        for i in warehouses for j in ports
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Supply constraints
    for i in warehouses:
        model.addConstr(
            gp.quicksum(x[i, j] for j in ports) <= supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints
    for j in ports:
        model.addConstr(
            gp.quicksum(x[i, j] for i in warehouses) >= demand[j],
            name=f"demand_{j}"
        )

    # Truck capacity constraint: containers on each route must be in multiples
    # such that x[i,j] <= trucks[i,j] * truck_capacity
    # Equivalently, introduce integer truck variables
    trucks = model.addVars(warehouses, ports, vtype=GRB.INTEGER, lb=0, name="trucks")
    for i in warehouses:
        for j in ports:
            model.addConstr(
                x[i, j] <= trucks[i, j] * truck_capacity,
                name=f"truck_cap_{i}_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}