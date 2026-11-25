import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]

    arcs_list = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),(0,6),(6,0),(0,7),(7,0),
        (1,2),(2,1),(1,5),(5,1),(1,6),(6,1),(2,3),(3,2),(2,6),(6,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),(4,7),(7,4),(5,6),(6,5),
        (5,7),(7,5),(6,7),(7,6)
    ]

    # commodities: (source, sink, demand), 0-indexed
    commodities_def = [
        (3, 7, demands[0]),  # Commodity 1
        (1, 5, demands[1]),  # Commodity 2
    ]

    arc_cap = {arcs_list[i]: arc_capacities[i] for i in range(len(arcs_list))}
    arc_cost = {arcs_list[i]: arc_unit_costs[i] for i in range(len(arcs_list))}

    model = gp.Model("multi_commodity_flow")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow[k][arc] for each commodity k and directed arc
    flow = {}
    for k in range(num_commodities):
        for arc in arcs_list:
            flow[(k, arc)] = model.addVar(lb=0.0, name=f"flow_{k}_{arc[0]}_{arc[1]}")

    model.update()

    # Objective: minimize total transmission cost
    model.setObjective(
        gp.quicksum(
            arc_cost[arc] * flow[(k, arc)]
            for k in range(num_commodities)
            for arc in arcs_list
        ),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for k in range(num_commodities):
        src, snk, demand = commodities_def[k]
        for node in range(num_nodes):
            out_arcs = [arc for arc in arcs_list if arc[0] == node]
            in_arcs  = [arc for arc in arcs_list if arc[1] == node]
            net_out = (
                gp.quicksum(flow[(k, arc)] for arc in out_arcs)
                - gp.quicksum(flow[(k, arc)] for arc in in_arcs)
            )
            if node == src:
                model.addConstr(net_out == demand, name=f"balance_k{k}_n{node}")
            elif node == snk:
                model.addConstr(net_out == -demand, name=f"balance_k{k}_n{node}")
            else:
                model.addConstr(net_out == 0.0, name=f"balance_k{k}_n{node}")

    # Capacity constraints: sum of all commodity flows <= arc capacity
    for arc in arcs_list:
        model.addConstr(
            gp.quicksum(flow[(k, arc)] for k in range(num_commodities)) <= arc_cap[arc],
            name=f"cap_{arc[0]}_{arc[1]}"
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