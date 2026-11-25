# IR: {"sets":{"facilities":"0..5","stores":"0..10"},"params":{"fixed_costs":"params['fixed_costs'][i]","shipping_costs_col0":"params['shipping_costs_col0'][i]","demands":"params['demands'][j]","capacities":"params['capacities'][i]"},"assumption":"Because only column 0 shipping costs are provided, use shipping_costs_col0[i] for every store j.","variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["sum_i shipped[i,j] == demands[j] for each store j","sum_j shipped[i,j] <= capacities[i]*opened[i] for each facility i"],"objective":"minimize sum_i fixed_costs[i]*opened[i] + sum_i,j shipping_costs_col0[i]*shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs_col0 = params["shipping_costs_col0"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 10)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={i: fixed_costs[i] for i in model.facilities},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        initialize={i: shipping_costs_col0[i] for i in model.facilities},
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.facility_capacity = pyo.Param(
        model.facilities,
        initialize={i: capacities[i] for i in model.facilities},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(model, j):
        return (
            sum(model.shipped[i, j] for i in model.facilities)
            == model.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(model, i):
        return (
            sum(model.shipped[i, j] for j in model.stores)
            <= model.facility_capacity[i] * model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.facilities, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i] * model.opened[i] for i in model.facilities
        )
        + sum(
            model.shipping_cost[i] * model.shipped[i, j]
            for i in model.facilities
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}