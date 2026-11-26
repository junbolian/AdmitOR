import gurobipy as gp
from gurobipy import GRB

def solve(params):
    painting_value = params["painting_value"]
    bust_value = params["bust_value"]
    vase_value = params["vase_value"]
    porsche_value = params["porsche_value"]
    diamond_value = params["diamond_value"]
    sofa_value = params["sofa_value"]
    dog_value = params["dog_value"]
    sculpture_value = params["sculpture_value"]
    boat_value = params["boat_value"]
    motorcycle_value = params["motorcycle_value"]
    cavour_furniture_value = params["cavour_furniture_value"]

    # Items and their values.
    # Indivisible single items: painting, bust, vase, porsche, sofa, sculpture, boat, motorcycle, cavour_furniture
    # Dogs: two dogs that must stay together (treated as a single bundle worth 2*dog_value)
    # Diamonds: three identical diamonds, each assigned independently (0, 1, 2, or 3 go to son 1)

    total_value = (painting_value + bust_value + vase_value + porsche_value +
                   3 * diamond_value + sofa_value + 2 * dog_value +
                   sculpture_value + boat_value + motorcycle_value + cavour_furniture_value)

    model = gp.Model("inheritance_partition")
    model.setParam("OutputFlag", 0)

    # Binary variable x_i = 1 means item i goes to son 1, 0 means son 2
    # Single indivisible items
    x_painting   = model.addVar(vtype=GRB.BINARY, name="x_painting")
    x_bust       = model.addVar(vtype=GRB.BINARY, name="x_bust")
    x_vase       = model.addVar(vtype=GRB.BINARY, name="x_vase")
    x_porsche    = model.addVar(vtype=GRB.BINARY, name="x_porsche")
    x_sofa       = model.addVar(vtype=GRB.BINARY, name="x_sofa")
    x_dogs       = model.addVar(vtype=GRB.BINARY, name="x_dogs")       # dogs bundle (must stay together)
    x_sculpture  = model.addVar(vtype=GRB.BINARY, name="x_sculpture")
    x_boat       = model.addVar(vtype=GRB.BINARY, name="x_boat")
    x_motorcycle = model.addVar(vtype=GRB.BINARY, name="x_motorcycle")
    x_cavour     = model.addVar(vtype=GRB.BINARY, name="x_cavour")

    # Integer variable for number of diamonds going to son 1 (0 to 3)
    n_diamonds   = model.addVar(vtype=GRB.INTEGER, lb=0, ub=3, name="n_diamonds")

    # Value assigned to son 1
    value_son1 = (painting_value   * x_painting   +
                  bust_value       * x_bust        +
                  vase_value       * x_vase        +
                  porsche_value    * x_porsche     +
                  sofa_value       * x_sofa        +
                  2 * dog_value    * x_dogs        +
                  sculpture_value  * x_sculpture   +
                  boat_value       * x_boat        +
                  motorcycle_value * x_motorcycle  +
                  cavour_furniture_value * x_cavour +
                  diamond_value    * n_diamonds)

    # Difference = total - 2 * value_son1; we minimize |total - 2*value_son1|
    # Introduce auxiliary variable for absolute difference
    diff = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="diff")

    model.addConstr(diff >= value_son1 - (total_value - value_son1), name="diff_pos")
    model.addConstr(diff >= (total_value - value_son1) - value_son1, name="diff_neg")

    model.setObjective(diff, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}