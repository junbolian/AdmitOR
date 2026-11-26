import gurobipy as gp
from gurobipy import GRB

def solve(params):
    A1_hours     = params["A1_hours"]
    A1_hours_II  = params["A1_hours_II"]
    A2_hours_I   = params["A2_hours_I"]
    A2_hours_II  = params["A2_hours_II"]
    A2_hours_III = params["A2_hours_III"]
    B1_hours_I   = params["B1_hours_I"]
    B1_hours_II  = params["B1_hours_II"]
    B2_hours_I   = params["B2_hours_I"]
    B2_hours_III = params["B2_hours_III"]
    B3_hours_I   = params["B3_hours_I"]

    cap_A1 = params["capacity_A1"]
    cap_A2 = params["capacity_A2"]
    cap_B1 = params["capacity_B1"]
    cap_B2 = params["capacity_B2"]
    cap_B3 = params["capacity_B3"]

    fc_A1 = params["full_load_cost_A1"]
    fc_A2 = params["full_load_cost_A2"]
    fc_B1 = params["full_load_cost_B1"]
    fc_B2 = params["full_load_cost_B2"]
    fc_B3 = params["full_load_cost_B3"]

    pc_A1 = params["proc_cost_A1"]
    pc_A2 = params["proc_cost_A2"]
    pc_B1 = params["proc_cost_B1"]
    pc_B2 = params["proc_cost_B2"]
    pc_B3 = params["proc_cost_B3"]

    raw_cost  = params["raw_material_cost"]   # per piece, same for I/II/III? 
    # Actually raw_material_cost is listed per product — but params has one value.
    # Per the table: I=0.25, II=0.35, III=0.5 — but params has a single key.
    # We'll treat it as a list/dict or scalar. Need to handle both.
    # Given the param name is singular, let's check: the problem says
    # "raw material cost per piece for products I, II, III" — likely a list [0.25, 0.35, 0.5]
    unit_price = params["unit_price"]  # similarly likely a list

    # Support both scalar and list/sequence for raw_cost and unit_price
    if hasattr(raw_cost, '__len__'):
        rc_I, rc_II, rc_III = raw_cost[0], raw_cost[1], raw_cost[2]
    else:
        rc_I = rc_II = rc_III = raw_cost

    if hasattr(unit_price, '__len__'):
        up_I, up_II, up_III = unit_price[0], unit_price[1], unit_price[2]
    else:
        up_I = up_II = up_III = unit_price

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # --- Decision variables ---
    # Pieces of product processed on each machine (continuous, >= 0)
    # Stage A
    xA1_I   = model.addVar(lb=0, name="xA1_I")    # product I on A1
    xA1_II  = model.addVar(lb=0, name="xA1_II")   # product II on A1
    xA2_I   = model.addVar(lb=0, name="xA2_I")    # product I on A2
    xA2_II  = model.addVar(lb=0, name="xA2_II")   # product II on A2
    xA2_III = model.addVar(lb=0, name="xA2_III")  # product III on A2

    # Stage B
    xB1_I   = model.addVar(lb=0, name="xB1_I")    # product I on B1
    xB1_II  = model.addVar(lb=0, name="xB1_II")   # product II on B1
    xB2_I   = model.addVar(lb=0, name="xB2_I")    # product I on B2
    xB2_III = model.addVar(lb=0, name="xB2_III")  # product III on B2
    xB3_I   = model.addVar(lb=0, name="xB3_I")    # product I on B3

    # Binary variables: 1 if machine is used (to trigger fixed cost)
    yA1 = model.addVar(vtype=GRB.BINARY, name="yA1")
    yA2 = model.addVar(vtype=GRB.BINARY, name="yA2")
    yB1 = model.addVar(vtype=GRB.BINARY, name="yB1")
    yB2 = model.addVar(vtype=GRB.BINARY, name="yB2")
    yB3 = model.addVar(vtype=GRB.BINARY, name="yB3")

    model.update()

    # --- Flow balance: total production per product must match across stages ---
    # Total product I produced = stage A total = stage B total
    prod_I_A  = xA1_I + xA2_I
    prod_I_B  = xB1_I + xB2_I + xB3_I
    prod_II_A = xA1_II + xA2_II
    prod_II_B = xB1_II                  # product II only on B1
    # product III only on A2 and B2
    prod_III_A = xA2_III
    prod_III_B = xB2_III

    # Stage A output must equal stage B input for each product
    model.addConstr(prod_I_A  == prod_I_B,  name="balance_I")
    model.addConstr(prod_II_A == prod_II_B, name="balance_II")
    model.addConstr(prod_III_A == prod_III_B, name="balance_III")

    # --- Machine capacity constraints ---
    model.addConstr(
        A1_hours * xA1_I + A1_hours_II * xA1_II <= cap_A1,
        name="cap_A1"
    )
    model.addConstr(
        A2_hours_I * xA2_I + A2_hours_II * xA2_II + A2_hours_III * xA2_III <= cap_A2,
        name="cap_A2"
    )
    model.addConstr(
        B1_hours_I * xB1_I + B1_hours_II * xB1_II <= cap_B1,
        name="cap_B1"
    )
    model.addConstr(
        B2_hours_I * xB2_I + B2_hours_III * xB2_III <= cap_B2,
        name="cap_B2"
    )
    model.addConstr(
        B3_hours_I * xB3_I <= cap_B3,
        name="cap_B3"
    )

    # --- Link binary usage variables to continuous production variables ---
    # If machine is not used (y=0), all flows through it must be 0
    # Big-M: use capacity / min_processing_time as upper bound on pieces
    M_A1  = cap_A1  / min(A1_hours, A1_hours_II)
    M_A2  = cap_A2  / min(A2_hours_I, A2_hours_II, A2_hours_III)
    M_B1  = cap_B1  / min(B1_hours_I, B1_hours_II)
    M_B2  = cap_B2  / min(B2_hours_I, B2_hours_III)
    M_B3  = cap_B3  / B3_hours_I

    model.addConstr(xA1_I  + xA1_II  <= M_A1 * yA1, name="link_A1")
    model.addConstr(xA2_I  + xA2_II  + xA2_III <= M_A2 * yA2, name="link_A2")
    model.addConstr(xB1_I  + xB1_II  <= M_B1 * yB1, name="link_B1")
    model.addConstr(xB2_I  + xB2_III <= M_B2 * yB2, name="link_B2")
    model.addConstr(xB3_I             <= M_B3 * yB3, name="link_B3")

    # --- Objective: maximize profit ---
    # Revenue
    revenue = (
        up_I   * prod_I_A
        + up_II  * prod_II_A
        + up_III * prod_III_A
    )

    # Raw material cost
    rm_cost = (
        rc_I   * prod_I_A
        + rc_II  * prod_II_A
        + rc_III * prod_III_A
    )

    # Processing costs (cost per machine hour * hours used on that machine)
    proc_cost = (
          pc_A1 * (A1_hours * xA1_I + A1_hours_II * xA1_II)
        + pc_A2 * (A2_hours_I * xA2_I + A2_hours_II * xA2_II + A2_hours_III * xA2_III)
        + pc_B1 * (B1_hours_I * xB1_I + B1_hours_II * xB1_II)
        + pc_B2 * (B2_hours_I * xB2_I + B2_hours_III * xB2_III)
        + pc_B3 * (B3_hours_I * xB3_I)
    )

    # Fixed (full-load) equipment costs — incurred if machine is used
    fixed_cost = (
        fc_A1 * yA1
        + fc_A2 * yA2
        + fc_B1 * yB1
        + fc_B2 * yB2
        + fc_B3 * yB3
    )

    model.setObjective(revenue - rm_cost - proc_cost - fixed_cost, GRB.MAXIMIZE)

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