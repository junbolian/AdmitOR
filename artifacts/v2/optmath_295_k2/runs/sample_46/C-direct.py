import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]        # list of 9 values for L_0..L_8
    operational_cost = params["operational_cost"]  # list of 9
    penalty_cost = params["penalty_cost"]    # list of 10 (OD pairs)
    demand = params["demand"]                # list of 10
    min_frequency = params["min_frequency"]  # scalar
    max_frequency = params["max_frequency"]  # scalar
    vehicle_capacity = params["vehicle_capacity"]  # scalar
    vehicle_usage = params["vehicle_usage"]  # list of 9

    # Lines: 0..8
    num_lines = 9
    lines = range(num_lines)

    # OD pairs (index order): OD_3_2, OD_2_0, OD_0_1, OD_1_3, OD_3_4,
    #                          OD_1_0, OD_1_4, OD_2_3, OD_4_3, OD_4_0
    num_od = 10
    od_pairs = range(num_od)

    # Lines serving each OD pair (from problem description)
    # OD_3_2(0): L0,L3,L4,L5,L6
    # OD_2_0(1): L2,L7,L8
    # OD_0_1(2): L0,L3,L5,L7
    # OD_1_3(3): L8
    # OD_3_4(4): L3,L6,L7,L8
    # OD_1_0(5): L2,L8
    # OD_1_4(6): L1,L5,L7
    # OD_2_3(7): L5
    # OD_4_3(8): L3,L5,L8
    # OD_4_0(9): L3,L5
    od_lines = {
        0: [0, 3, 4, 5, 6],
        1: [2, 7, 8],
        2: [0, 3, 5, 7],
        3: [8],
        4: [3, 6, 7, 8],
        5: [2, 8],
        6: [1, 5, 7],
        7: [5],
        8: [3, 5, 8],
        9: [3, 5],
    }

    # Stations and lines passing through each (for transfer station constraints)
    # Station 0: L3,L4,L5,L7,L8
    # Station 1: L1,L4
    # Station 2: L1,L6
    # Station 3: (none that allow transfer)
    # Station 4: L0,L3,L4
    station_lines = {
        0: [3, 4, 5, 7, 8],
        1: [1, 4],
        2: [1, 6],
        3: [],
        4: [0, 3, 4],
    }
    num_stations = 5

    model = gp.Model("transit")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[l]: binary, whether line l is selected
    y = model.addVars(num_lines, vtype=GRB.BINARY, name="y")

    # f[l]: continuous frequency of line l (0 if not selected)
    f = model.addVars(num_lines, lb=0.0, name="f")

    # u[od]: unmet demand for OD pair od
    u = model.addVars(num_od, lb=0.0, name="u")

    # t[s]: binary, whether station s is a transfer station
    t = model.addVars(num_stations, vtype=GRB.BINARY, name="t")

    # Objective: fixed costs + operational costs + penalty costs
    obj = (
        gp.quicksum(fixed_cost[l] * y[l] for l in lines)
        + gp.quicksum(operational_cost[l] * f[l] for l in lines)
        + gp.quicksum(penalty_cost[od] * u[od] for od in od_pairs)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Frequency bounds: min_frequency * y[l] <= f[l] <= max_frequency * y[l]
    for l in lines:
        model.addConstr(f[l] >= min_frequency * y[l], name=f"freq_min_{l}")
        model.addConstr(f[l] <= max_frequency * y[l], name=f"freq_max_{l}")

    # Vehicle capacity constraint
    model.addConstr(
        gp.quicksum(vehicle_usage[l] * f[l] for l in lines) <= vehicle_capacity,
        name="vehicle_cap"
    )

    # Demand coverage constraints:
    # sum of frequencies of serving lines + unmet demand >= demand[od]
    for od in od_pairs:
        model.addConstr(
            gp.quicksum(f[l] for l in od_lines[od]) + u[od] >= demand[od],
            name=f"demand_{od}"
        )

    # Transfer station constraints:
    # t[s] can be 1 only if at least 2 lines from station_lines[s] are selected
    for s in range(num_stations):
        sl = station_lines[s]
        if len(sl) == 0:
            # Station 3: cannot be transfer station
            model.addConstr(t[s] == 0, name=f"no_transfer_{s}")
        else:
            # t[s] <= (sum of y[l] for l in station_lines[s]) / 2
            # i.e., t[s] = 1 requires at least 2 lines active
            model.addConstr(
                t[s] * 2 <= gp.quicksum(y[l] for l in sl),
                name=f"transfer_min2_{s}"
            )
            # t[s] is bounded by available lines
            model.addConstr(
                t[s] <= len(sl),
                name=f"transfer_ub_{s}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}