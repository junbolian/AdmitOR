import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    supply = params["supply"]      # list of 6 values (warehouses)
    demand = params["demand"]      # list of 5 values (ports)
    distance = params["distance"]  # 6x5 matrix
    cost_rate = params["cost_rate"]
    truck_capacity = params["truck_capacity"]

    num_warehouses = 6
    num_ports = 5

    warehouses = range(num_warehouses)
    ports = range(num_ports)

    model = gp.Model("container_transport")
    model.setParam("OutputFlag", 0)

    # Number of trucks sent from warehouse i to port j (integer)
    # Each truck carries up to truck_capacity containers
    trucks = model.addVars(warehouses, ports, vtype=GRB.INTEGER, lb=0, name="trucks")

    # Containers transported from warehouse i to port j
    containers = model.addVars(warehouses, ports, vtype=GRB.INTEGER, lb=0, name="containers")

    # Objective: minimize total cost = cost_rate * distance * num_trucks
    # Cost is per truck per km (truck carries containers, cost is per container per km,
    # but since each truck trip costs cost_rate * distance regardless of load,
    # and we want to minimize cost per container transported, the cost is
    # cost_rate * distance[i][j] * trucks[i][j] for each route)
    # Re-reading: "cost to transport each container is proportional to the distance,
    # with a rate of 30 euros per kilometer" => cost = cost_rate * distance * containers
    model.setObjective(
        gp.quicksum(
            cost_rate * distance[i][j] * containers[i, j]
            for i in warehouses for j in ports
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: containers shipped from each warehouse <= supply
    for i in warehouses:
        model.addConstr(
            gp.quicksum(containers[i, j] for j in ports) <= supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: containers received at each port == demand
    for j in ports:
        model.addConstr(
            gp.quicksum(containers[i, j] for i in warehouses) == demand[j],
            name=f"demand_{j}"
        )

    # Truck capacity constraints: containers on each route <= trucks * truck_capacity
    for i in warehouses:
        for j in ports:
            model.addConstr(
                containers[i, j] <= trucks[i, j] * truck_capacity,
                name=f"truck_cap_{i}_{j}"
            )

    # Each truck carries at least 1 container (no empty trucks)
    # i.e., trucks[i,j] <= containers[i,j] (can't have more trucks than containers)
    for i in warehouses:
        for j in ports:
            model.addConstr(
                trucks[i, j] <= containers[i, j],
                name=f"no_empty_truck_{i}_{j}"
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