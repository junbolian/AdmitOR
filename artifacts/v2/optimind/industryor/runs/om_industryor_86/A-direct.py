import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    m1_liq = params["machine1_time_liquid"]
    m2_liq = params["machine2_time_liquid"]
    m1_sol = params["machine1_time_solid"]
    m2_sol = params["machine2_time_solid"]
    init_liq = params["initial_inventory_liquid"]
    init_sol = params["initial_inventory_solid"]
    cap1 = params["machine1_capacity_hours"]
    cap2 = params["machine2_capacity_hours"]
    dem_liq = params["demand_liquid"]
    dem_sol = params["demand_solid"]

    model = pyo.ConcreteModel()

    model.prod_liquid = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.prod_solid = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Machine 1 time (minutes): capacity in hours * 60
    model.m1_constraint = pyo.Constraint(
        expr=m1_liq * model.prod_liquid + m1_sol * model.prod_solid <= cap1 * 60
    )
    # Machine 2 time (minutes)
    model.m2_constraint = pyo.Constraint(
        expr=m2_liq * model.prod_liquid + m2_sol * model.prod_solid <= cap2 * 60
    )
    # Demand satisfaction (end-of-week inventory must be >= 0)
    model.dem_liq_constraint = pyo.Constraint(
        expr=init_liq + model.prod_liquid >= dem_liq
    )
    model.dem_sol_constraint = pyo.Constraint(
        expr=init_sol + model.prod_solid >= dem_sol
    )

    # Objective: maximize end-of-week inventory
    model.obj = pyo.Objective(
        expr=(init_liq + model.prod_liquid - dem_liq)
        + (init_sol + model.prod_solid - dem_sol),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}