import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    labor_adv = params["labor_hours_advanced"]
    insp_adv = params["inspection_hours_advanced"]
    profit_adv = params["profit_advanced"]
    labor_int = params["labor_hours_intermediate"]
    insp_int = params["inspection_hours_intermediate"]
    profit_int = params["profit_intermediate"]
    labor_bsc = params["labor_hours_basic"]
    insp_bsc = params["inspection_hours_basic"]
    profit_bsc = params["profit_basic"]
    labor_cap = params["labor_capacity"]
    insp_cap = params["inspection_capacity"]
    dem_adv = params["demand_advanced"]
    dem_int = params["demand_intermediate"]
    dem_bsc = params["demand_basic"]

    model = pyo.ConcreteModel()

    model.x_adv = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_int = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_bsc = pyo.Var(domain=pyo.NonNegativeReals)

    model.labor_con = pyo.Constraint(
        expr=labor_adv * model.x_adv
        + labor_int * model.x_int
        + labor_bsc * model.x_bsc
        <= labor_cap
    )
    model.insp_con = pyo.Constraint(
        expr=insp_adv * model.x_adv
        + insp_int * model.x_int
        + insp_bsc * model.x_bsc
        <= insp_cap
    )
    model.dem_adv_con = pyo.Constraint(expr=model.x_adv <= dem_adv)
    model.dem_int_con = pyo.Constraint(expr=model.x_int <= dem_int)
    model.dem_bsc_con = pyo.Constraint(expr=model.x_bsc <= dem_bsc)

    model.obj = pyo.Objective(
        expr=profit_adv * model.x_adv
        + profit_int * model.x_int
        + profit_bsc * model.x_bsc,
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}