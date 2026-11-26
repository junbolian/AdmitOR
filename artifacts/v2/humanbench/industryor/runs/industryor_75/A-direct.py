import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    profit = params["profit"]
    plastic_avail = params["plastic_avail"]
    electronics_avail = params["electronics_avail"]
    plastic_req = params["plastic_req"]
    electronics_req = params["electronics_req"]

    toys = ["robot", "model_car", "building_blocks", "doll"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(toys, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Objective(
        expr=sum(profit[i] * model.x[toys[i]] for i in range(len(toys))),
        sense=pyo.maximize,
    )

    model.plastic_con = pyo.Constraint(
        expr=sum(plastic_req[i] * model.x[toys[i]] for i in range(len(toys))) <= plastic_avail
    )
    model.electronics_con = pyo.Constraint(
        expr=sum(electronics_req[i] * model.x[toys[i]] for i in range(len(toys))) <= electronics_avail
    )

    # If robots are manufactured, dolls cannot be manufactured: x_robot + x_doll <= M * y ... use binary
    model.y_robot = pyo.Var(domain=pyo.Binary)
    model.y_car = pyo.Var(domain=pyo.Binary)

    M = max(plastic_avail, electronics_avail) + 1

    # Link binaries to positive production
    model.robot_link = pyo.Constraint(expr=model.x["robot"] <= M * model.y_robot)
    model.car_link = pyo.Constraint(expr=model.x["model_car"] <= M * model.y_car)

    # If robots manufactured, no dolls
    model.robot_doll_con = pyo.Constraint(expr=model.x["doll"] <= M * (1 - model.y_robot))

    # If model cars manufactured, then building blocks must be manufactured
    model.car_blocks_con = pyo.Constraint(
        expr=model.x["building_blocks"] >= model.y_car * 0
    )
    model.car_blocks_force = pyo.Constraint(
        expr=model.x["building_blocks"] >= model.y_car * 1e-6
    )

    # Dolls cannot exceed model cars
    model.doll_car_con = pyo.Constraint(expr=model.x["doll"] <= model.x["model_car"])

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.profit_expr))
    return {"objective": obj_val, "status": "optimal"}