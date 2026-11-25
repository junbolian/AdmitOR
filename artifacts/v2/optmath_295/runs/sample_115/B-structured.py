# IR: {"sets":{"warehouses":"0..5","stores":"0..5"},"params":{"supplies":"nonnegative supply[warehouse] from params['supplies']","demands":"nonnegative demand[store] from params['demands']","costs":"real cost[warehouse,store] from params['costs']"},"variables":{"ship[warehouse,store]":"continuous, nonnegative"},"constraints":["For each warehouse: sum_store ship[warehouse,store] = supplies[warehouse]","For each store: sum_warehouse ship[warehouse,store] = demands[store]"],"objective":"Minimize sum_warehouse,store costs[warehouse,store] * ship[warehouse,store]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 5)

    model.supplies = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: params["supplies"][warehouse]
            for warehouse in model.warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.demands = pyo.Param(
        model.stores,
        initialize={
            store: params["demands"][store]
            for store in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.costs = pyo.Param(
        model.warehouses,
        model.stores,
        initialize={
            (warehouse, store): params["costs"][warehouse][store]
            for warehouse in model.warehouses
            for store in model.stores
        },
        within=pyo.Reals,
    )

    model.ship = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, warehouse):
        return (
            sum(mdl.ship[warehouse, store] for store in mdl.stores)
            == mdl.supplies[warehouse]
        )

    def demand_rule(mdl, store):
        return (
            sum(mdl.ship[warehouse, store] for warehouse in mdl.warehouses)
            == mdl.demands[store]
        )

    model.supply_constraints = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )
    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[warehouse, store] * model.ship[warehouse, store]
            for warehouse in model.warehouses
            for store in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}