import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # shipping_cost indexed as [c][p][d][z]
    shipping_cost = params["shipping_cost"]
    fixed_cost_dc = params["fixed_cost_dc"]
    throughput_cost = params["throughput_cost"]
    plant_supply = params["plant_supply"]
    demand = params["demand"]
    dc_min_throughput = params["dc_min_throughput"]
    dc_max_throughput = params["dc_max_throughput"]

    num_commodities = 3
    num_plants = 2
    num_dcs = 2
    num_zones = 4

    commodities = range(num_commodities)
    plants = range(num_plants)
    dcs = range(num_dcs)
    zones = range(num_zones)

    # Helper to safely extract nested or flat values
    def get_sc(c, p, d, z):
        val = shipping_cost
        for idx in (c, p, d, z):
            val = val[idx]
        return float(val)

    def get_tc(d, z):
        val = throughput_cost[d][z]
        return float(val)

    def get_supply(p, c):
        return float(plant_supply[p][c])

    def get_demand(c, z):
        return float(demand[c][z])

    def get_fixed(d):
        return float(fixed_cost_dc[d])

    def get_min_tp(d):
        return float(dc_min_throughput[d])

    def get_max_tp(d):
        return float(dc_max_throughput[d])

    model = gp.Model("distribution")
    model.setParam("OutputFlag", 0)

    # x[c, p, d, z]: units of commodity c shipped from plant p through dc d to zone z
    x = {}
    for c in commodities:
        for p in plants:
            for d in dcs:
                for z in zones:
                    x[c, p, d, z] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                                  name=f"x_{c}_{p}_{d}_{z}")

    # y[d]: binary, 1 if dc d is open
    y = {}
    for d in dcs:
        y[d] = model.addVar(vtype=GRB.BINARY, name=f"y_{d}")

    # a[d, z]: binary, 1 if zone z is assigned to dc d
    a = {}
    for d in dcs:
        for z in zones:
            a[d, z] = model.addVar(vtype=GRB.BINARY, name=f"a_{d}_{z}")

    # Objective
    shipping_expr = gp.quicksum(
        get_sc(c, p, d, z) * x[c, p, d, z]
        for c in commodities for p in plants for d in dcs for z in zones
    )

    fixed_expr = gp.quicksum(get_fixed(d) * y[d] for d in dcs)

    # Throughput cost: cost per dc per zone * total demand through dc d for zone z
    # Total demand served by dc d for zone z = sum_c(demand[c][z]) * a[d,z]
    throughput_expr = gp.quicksum(
        get_tc(d, z) * sum(get_demand(c, z) for c in commodities) * a[d, z]
        for d in dcs for z in zones
    )

    model.setObjective(shipping_expr + fixed_expr + throughput_expr, GRB.MINIMIZE)

    # Supply constraints
    for p in plants:
        for c in commodities:
            model.addConstr(
                gp.quicksum(x[c, p, d, z] for d in dcs for z in zones) <= get_supply(p, c),
                name=f"supply_{p}_{c}"
            )

    # Demand constraints: shipment through dc d to zone z >= demand * assignment
    for c in commodities:
        for d in dcs:
            for z in zones:
                model.addConstr(
                    gp.quicksum(x[c, p, d, z] for p in plants) >= get_demand(c, z) * a[d, z],
                    name=f"demand_{c}_{d}_{z}"
                )

    # Zone assignment: each zone assigned to exactly one dc
    for z in zones:
        model.addConstr(
            gp.quicksum(a[d, z] for d in dcs) == 1,
            name=f"zone_assign_{z}"
        )

    # If zone z assigned to dc d, dc d must be open
    for d in dcs:
        for z in zones:
            model.addConstr(a[d, z] <= y[d], name=f"open_{d}_{z}")

    # DC throughput bounds (only binding when dc is open)
    for d in dcs:
        throughput_d = gp.quicksum(
            sum(get_demand(c, z) for c in commodities) * a[d, z]
            for z in zones
        )
        model.addConstr(throughput_d >= get_min_tp(d) * y[d], name=f"min_tp_{d}")
        model.addConstr(throughput_d <= get_max_tp(d) * y[d], name=f"max_tp_{d}")

    # Big-M: shipment can only flow through assigned dc
    big_M = max(get_supply(p, c) for p in plants for c in commodities)
    for c in commodities:
        for p in plants:
            for d in dcs:
                for z in zones:
                    model.addConstr(
                        x[c, p, d, z] <= big_M * a[d, z],
                        name=f"bigM_{c}_{p}_{d}_{z}"
                    )

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