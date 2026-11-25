import gurobipy as gp
from gurobipy import GRB


def solve(params):
    node_coordinates = params["node_coordinates"]
    farm_supply = params["farm_supply"]      # supplies for farms 0,1,2
    retail_demand = params["retail_demand"]  # demands for retail centers 3,4,5,6
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    farms = [0, 1, 2]
    retailers = [3, 4, 5, 6]
    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    model = gp.Model("perishable_logistics")
    model.Params.OutputFlag = 0

    # Flow on each directed arc, bounded by arc capacity.
    x = {}
    for idx, (i, j) in enumerate(arcs):
        x[i, j] = model.addVar(
            lb=0.0,
            ub=arc_capacities[idx],
            vtype=GRB.CONTINUOUS,
            name=f"x_{i}_{j}",
        )

    # Minimize total spoilage-adjusted transport cost.
    model.setObjective(
        gp.quicksum(
            arc_unit_costs[idx] * x[arcs[idx][0], arcs[idx][1]]
            for idx in range(len(arcs))
        ),
        GRB.MINIMIZE,
    )

    # Farm supply: every unit of harvest must be dispatched (equality).
    for fi, f in enumerate(farms):
        model.addConstr(
            gp.quicksum(x[f, j] for j in retailers) == farm_supply[fi],
            name=f"supply_{f}",
        )

    # Retailer demand: each center must receive exactly its required units (equality).
    for ri, r in enumerate(retailers):
        model.addConstr(
            gp.quicksum(x[i, r] for i in farms) == retail_demand[ri],
            name=f"demand_{r}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": "failed"}