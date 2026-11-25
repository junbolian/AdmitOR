import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    commodity_supply = params["commodity_supply"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    # Directed arcs in fixed order
    arcs = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),
        (1,2),(2,1),(1,7),(7,1),
        (2,3),(3,2),(2,6),(6,2),(2,7),(7,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5),(6,7),(7,6),(7,8),(8,7)
    ]

    arc_index = {a: i for i, a in enumerate(arcs)}

    # Outgoing and incoming arc indices per node
    out_arcs = {n: [] for n in range(num_nodes)}
    in_arcs  = {n: [] for n in range(num_nodes)}
    for i, (u, v) in enumerate(arcs):
        out_arcs[u].append(i)
        in_arcs[v].append(i)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: f[k][a] = flow of commodity k on arc a
    f = []
    for k in range(num_commodities):
        f_k = model.addVars(num_arcs, lb=0.0, name=f"f_{k}")
        f.append(f_k)

    # Auxiliary variable: maximum utilization rate
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Flow conservation constraints
    for k in range(num_commodities):
        src = commodity_source[k]
        snk = commodity_sink[k]
        supply = commodity_supply[k]
        for n in range(num_nodes):
            if n == src:
                rhs = supply
            elif n == snk:
                rhs = -supply
            else:
                rhs = 0.0
            model.addConstr(
                gp.quicksum(f[k][a] for a in out_arcs[n]) -
                gp.quicksum(f[k][a] for a in in_arcs[n]) == rhs,
                name=f"flow_cons_k{k}_n{n}"
            )

    # Capacity and utilization constraints
    for a in range(num_arcs):
        cap = arc_capacities[a]
        total_flow = gp.quicksum(f[k][a] for k in range(num_commodities))
        # Aggregate capacity
        model.addConstr(total_flow <= cap, name=f"cap_{a}")
        # Utilization rate <= z
        model.addConstr(total_flow <= z * cap, name=f"util_{a}")

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