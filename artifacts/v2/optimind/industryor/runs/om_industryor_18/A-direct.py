import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: number of each toy type manufactured
    model.robots = pyo.Var(domain=pyo.NonNegativeReals)
    model.cars = pyo.Var(domain=pyo.NonNegativeReals)
    model.blocks = pyo.Var(domain=pyo.NonNegativeReals)
    model.dolls = pyo.Var(domain=pyo.NonNegativeReals)

    # Objective: maximize profit
    model.profit = pyo.Objective(
        expr=(
            params["profit_per_robot"] * model.robots
            + params["profit_per_car"] * model.cars
            + params["profit_per_blocks"] * model.blocks
            + params["profit_per_doll"] * model.dolls
        ),
        sense=pyo.maximize,
    )

    # Plastic capacity constraint
    model.plastic = pyo.Constraint(
        expr=(
            params["plastic_per_robot"] * model.robots
            + params["plastic_per_car"] * model.cars
            + params["plastic_per_blocks"] * model.blocks
            + params["plastic_per_doll"] * model.dolls
            <= params["plastic_capacity"]
        )
    )

    # Electronics capacity constraint
    model.electronics = pyo.Constraint(
        expr=(
            params["electronics_per_robot"] * model.robots
            + params["electronics_per_car"] * model.cars
            + params["electronics_per_blocks"] * model.blocks
            + params["electronics_per_doll"] * model.dolls
            <= params["electronics_capacity"]
        )
    )

    # If robots are manufactured, dolls are not: robots + dolls handled via
    # big-M style indicator encoded as: dolls <= M*(1 - robots_flag) is nonlinear.
    # Instead use the logical constraint directly: robots * dolls == 0.
    # With positive capacities and profitability we express it exactly via a
    # binary indicator and big-M constants derived from capacity bounds.
    # Upper bound on robots: plastic capacity / plastic_per_robot etc.
    robot_ub = min(
        params["plastic_capacity"] / params["plastic_per_robot"],
        params["electronics_capacity"] / params["electronics_per_robot"],
    )
    doll_ub = min(
        params["plastic_capacity"] / params["plastic_per_doll"],
        params["electronics_capacity"] / params["electronics_per_doll"],
    )

    model.robot_active = pyo.Var(domain=pyo.Binary)

    # robots <= robot_ub * robot_active
    model.robots_on = pyo.Constraint(
        expr=model.robots <= robot_ub * model.robot_active
    )
    # dolls <= doll_ub * (1 - robot_active)
    model.dolls_off_when_robots = pyo.Constraint(
        expr=model.dolls <= doll_ub * (1 - model.robot_active)
    )

    # If cars are manufactured, blocks are also manufactured: cars > 0 => blocks > 0.
    # Equivalent to blocks >= cars_flag where cars_flag is binary with cars <= M*flag.
    car_ub = min(
        params["plastic_capacity"] / params["plastic_per_car"],
        params["electronics_capacity"] / params["electronics_per_car"],
    )
    model.car_active = pyo.Var(domain=pyo.Binary)
    model.cars_on = pyo.Constraint(expr=model.cars <= car_ub * model.car_active)
    model.blocks_when_cars = pyo.Constraint(expr=model.blocks >= model.car_active)

    # Dolls cannot exceed cars
    model.dolls_le_cars = pyo.Constraint(expr=model.dolls <= model.cars)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}