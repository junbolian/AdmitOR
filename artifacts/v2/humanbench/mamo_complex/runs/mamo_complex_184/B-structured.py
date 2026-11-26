# IR: {"sets":{"centers":[0,1,2,3,4,5,6],"stores":[0,1,2,3,4,5,6,7,8]},"params":{"opening_cost_center_1":"fixed cost for center 0","opening_cost_center_2":"fixed cost for center 1","opening_cost_center_3":"fixed cost for center 2","opening_cost_center_4":"fixed cost for center 3","opening_cost_center_5":"fixed cost for center 4","opening_cost_center_6":"fixed cost for center 5","opening_cost_center_7":"fixed cost for center 6","transportation_cost_matrix":"7x9 route costs, indexed [center][store]","store_demand":"9 store demands","center_capacity":"7 center capacities"},"variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipped[i,j] = store_demand[j]","For each center i: sum_j shipped[i,j] <= center_capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i] * opened[i] + sum_i sum_j transportation_cost_matrix[i][j] * shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the capacitated facility-location problem using zero-based arrays."""
    opening_costs = [
        params["opening_cost_center_1"],
        params["opening_cost_center_2"],
        params["opening_cost_center_3"],
        params["opening_cost_center_4"],
        params["opening_cost_center_5"],
        params["opening_cost_center_6"],
        params["opening_cost_center_7"],
    ]
    transportation_costs = params["transportation_cost_matrix"]
    demands = params["store_demand"]
    capacities = params["center_capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 6)
    model.stores = pyo.RangeSet(0, 8)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: opening_costs[i],
        within=pyo.Reals,
    )
    model.transportation_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: transportation_costs[i][j],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demands[j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: capacities[i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return sum(
            mdl.shipped[i, j] for i in mdl.centers
        ) == mdl.demand[j]

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return sum(
            mdl.shipped[i, j] for j in mdl.stores
        ) <= mdl.capacity[i] * mdl.opened[i]

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transportation_cost[i, j] * model.shipped[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this specific error when no feasible solution loads.
        # Re-raise unexpected solver errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}