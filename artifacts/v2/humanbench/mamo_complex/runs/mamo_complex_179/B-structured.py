# IR: {"sets":{"DCs":"0..4","Stores":"0..4"},"params":{"opening_cost":"DCs -> nonnegative real","transport_cost":"DCs x Stores -> nonnegative real","store_demand":"Stores -> nonnegative real","dc_capacity":"DCs -> nonnegative real"},"variables":{"opened":"DCs -> binary","shipped":"DCs x Stores -> nonnegative real"},"constraints":["For each store j: sum_i shipped[i,j] = store_demand[j]","For each DC i: sum_j shipped[i,j] <= dc_capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i] * opened[i] + sum_i,j transport_cost[i,j] * shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-five vectors and a 5-by-5 transportation matrix."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    store_demand = params["store_demand"]
    dc_capacity = params["dc_capacity"]

    model = pyo.ConcreteModel()

    model.DCs = pyo.RangeSet(0, 4)
    model.Stores = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.DCs,
        initialize={i: opening_cost[i] for i in model.DCs},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DCs,
        model.Stores,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.DCs
            for j in model.Stores
        },
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.Stores,
        initialize={j: store_demand[j] for j in model.Stores},
        within=pyo.NonNegativeReals,
    )
    model.dc_capacity = pyo.Param(
        model.DCs,
        initialize={i: dc_capacity[i] for i in model.DCs},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DCs, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.DCs, model.Stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(network, j):
        return (
            sum(network.shipped[i, j] for i in network.DCs)
            == network.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.Stores, rule=demand_rule
    )

    def capacity_rule(network, i):
        return (
            sum(network.shipped[i, j] for j in network.Stores)
            <= network.dc_capacity[i] * network.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.DCs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.DCs
            )
            + sum(
                model.transport_cost[i, j] * model.shipped[i, j]
                for i in model.DCs
                for j in model.Stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}