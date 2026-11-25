import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---------- parameter extraction ----------
    cost_p0_0to1 = params["cost_p0_0to1"]
    cost_p0_1to0 = params["cost_p0_1to0"]
    cost_p1_0to1 = params["cost_p1_0to1"]
    cost_p1_1to0 = params["cost_p1_1to0"]

    max_planes_p0 = params["max_planes_p0"]
    max_planes_p1 = params["max_planes_p1"]

    demand_0to1 = params["demand_0to1"]

    capacity_p0 = params["capacity_p0"]
    capacity_p1 = params["capacity_p1"]

    max_ops_p0_0to1 = params["max_ops_p0_0to1"]
    max_ops_p1_0to1 = params["max_ops_p1_0to1"]
    max_ops_p0_1to0 = params["max_ops_p0_1to0"]
    max_ops_p1_1to0 = params["max_ops_p1_1to0"]

    # ---------- model ----------
    model = pyo.ConcreteModel()

    # decision variables: number of planes operated on each route
    model.x_p0_0to1 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x_p0_1to0 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x_p1_0to1 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x_p1_1to0 = pyo.Var(domain=pyo.NonNegativeIntegers)

    # idle planes at each location
    model.idle_p0_0 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.idle_p0_1 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.idle_p1_0 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.idle_p1_1 = pyo.Var(domain=pyo.NonNegativeIntegers)

    # ---------- objective ----------
    model.total_cost = pyo.Objective(
        expr=(
            cost_p0_0to1 * model.x_p0_0to1
            + cost_p0_1to0 * model.x_p0_1to0
            + cost_p1_0to1 * model.x_p1_0to1
            + cost_p1_1to0 * model.x_p1_1to0
        ),
        sense=pyo.minimize,
    )

    # ---------- constraints ----------

    # demand satisfaction from Location 0 to Location 1
    model.demand_sat = pyo.Constraint(
        expr=capacity_p0 * model.x_p0_0to1 + capacity_p1 * model.x_p1_0to1
        >= demand_0to1
    )

    # fleet availability: total planes of each type across both locations
    model.fleet_p0 = pyo.Constraint(
        expr=model.x_p0_0to1 + model.x_p0_1to0
        + model.idle_p0_0 + model.idle_p0_1
        <= max_planes_p0
    )
    model.fleet_p1 = pyo.Constraint(
        expr=model.x_p1_0to1 + model.x_p1_1to0
        + model.idle_p1_0 + model.idle_p1_1
        <= max_planes_p1
    )

    # initial idle allocation balance at each location
    # idle at location 0 = arriving planes + planes remaining idle at location 0
    # (planes leaving location 0 reduce idle count, so idle_prev = departing + idle_now)
    # Here: planes available at loc 0 (idle_p0_0) must equal planes departing from loc0 to loc1
    # plus planes staying idle.
    model.init_bal_p0_0 = pyo.Constraint(
        expr=model.idle_p0_0 == model.x_p0_0to1 + model.idle_p0_0
    )
    model.init_bal_p1_0 = pyo.Constraint(
        expr=model.idle_p1_0 == model.x_p1_0to1 + model.idle_p1_0
    )
    model.init_bal_p0_1 = pyo.Constraint(
        expr=model.idle_p0_1 == model.x_p0_1to0 + model.idle_p0_1
    )
    model.init_bal_p1_1 = pyo.Constraint(
        expr=model.idle_p1_1 == model.x_p1_1to0 + model.idle_p1_1
    )

    # route operation limits
    model.lim_p0_0to1 = pyo.Constraint(expr=model.x_p0_0to1 <= max_ops_p0_0to1)
    model.lim_p1_0to1 = pyo.Constraint(expr=model.x_p1_0to1 <= max_ops_p1_0to1)
    model.lim_p0_1to0 = pyo.Constraint(expr=model.x_p0_1to0 <= max_ops_p0_1to0)
    model.lim_p1_1to0 = pyo.Constraint(expr=model.x_p1_1to0 <= max_ops_p1_1to0)

    # ---------- solve ----------
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}