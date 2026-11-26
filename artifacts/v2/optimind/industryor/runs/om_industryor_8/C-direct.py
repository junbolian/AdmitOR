def solve(params):
    import gurobipy as gp
    from gurobipy import GRB

    profit_truck    = params["profit_truck"]
    profit_airplane = params["profit_airplane"]
    profit_boat     = params["profit_boat"]
    profit_train    = params["profit_train"]

    wood_capacity  = params["wood_capacity"]
    wood_truck     = params["wood_truck"]
    wood_airplane  = params["wood_airplane"]
    wood_boat      = params["wood_boat"]
    wood_train     = params["wood_train"]

    steel_capacity  = params["steel_capacity"]
    steel_truck     = params["steel_truck"]
    steel_airplane  = params["steel_airplane"]
    steel_boat      = params["steel_boat"]
    steel_train     = params["steel_train"]

    model = gp.Model("haus_toys")
    model.setParam("OutputFlag", 0)

    # Continuous production quantities
    x_truck    = model.addVar(lb=0, name="x_truck")
    x_airplane = model.addVar(lb=0, name="x_airplane")
    x_boat     = model.addVar(lb=0, name="x_boat")
    x_train    = model.addVar(lb=0, name="x_train")

    # Binary indicators: y_i = 1 if toy type i is manufactured
    y_truck    = model.addVar(vtype=GRB.BINARY, name="y_truck")
    y_airplane = model.addVar(vtype=GRB.BINARY, name="y_airplane")
    y_boat     = model.addVar(vtype=GRB.BINARY, name="y_boat")
    y_train    = model.addVar(vtype=GRB.BINARY, name="y_train")

    # Objective: maximize profit
    model.setObjective(
        profit_truck    * x_truck
        + profit_airplane * x_airplane
        + profit_boat     * x_boat
        + profit_train    * x_train,
        GRB.MAXIMIZE
    )

    # Resource constraints
    model.addConstr(
        wood_truck  * x_truck
        + wood_airplane * x_airplane
        + wood_boat     * x_boat
        + wood_train    * x_train
        <= wood_capacity,
        name="wood"
    )
    model.addConstr(
        steel_truck  * x_truck
        + steel_airplane * x_airplane
        + steel_boat     * x_boat
        + steel_train    * x_train
        <= steel_capacity,
        name="steel"
    )

    # Big-M linking: production only if binary indicator is 1
    # Upper bounds derived from binding resource constraints
    M_truck    = min(wood_capacity / wood_truck,    steel_capacity / steel_truck)
    M_airplane = min(wood_capacity / wood_airplane, steel_capacity / steel_airplane)
    M_boat     = min(wood_capacity / wood_boat,     steel_capacity / steel_boat)
    M_train    = min(wood_capacity / wood_train,    steel_capacity / steel_train)

    model.addConstr(x_truck    <= M_truck    * y_truck,    name="link_truck")
    model.addConstr(x_airplane <= M_airplane * y_airplane, name="link_airplane")
    model.addConstr(x_boat     <= M_boat     * y_boat,     name="link_boat")
    model.addConstr(x_train    <= M_train    * y_train,    name="link_train")

    # If trucks are manufactured, trains are not: y_truck + y_train <= 1
    model.addConstr(y_truck + y_train <= 1, name="truck_no_train")

    # If boats are manufactured, airplanes must also be manufactured: y_boat <= y_airplane
    model.addConstr(y_boat <= y_airplane, name="boat_requires_airplane")

    # Boats cannot exceed trains in quantity: x_boat <= x_train
    model.addConstr(x_boat <= x_train, name="boat_le_train")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}