# IR: {"sets":{"customers":"0..14","lockers":"0..5"},"params":{"installation_cost":"locker-indexed nonnegative fixed costs","volume_capacity":"locker-indexed nonnegative capacities","customer_demand":"customer-indexed nonnegative demands","delivery_cost_matrix":"15x6 nonnegative assignment costs, not multiplied by demand","locker_coordinates_x":"locker-indexed real coordinates; informational","locker_coordinates_y":"locker-indexed real coordinates; informational","customer_coordinates_x":"customer-indexed real coordinates; informational","customer_coordinates_y":"customer-indexed real coordinates; informational"},"variables":{"opened[j]":"binary","assigned[i,j]":"binary"},"constraints":["For each customer i: sum_j assigned[i,j] = 1.","For each locker j: sum_i customer_demand[i]*assigned[i,j] <= volume_capacity[j]*opened[j].","For each customer i and locker j: assigned[i,j] <= opened[j]."],"objective":"Minimize sum_j installation_cost[j]*opened[j] + sum_i,j delivery_cost_matrix[i,j]*assigned[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    installation_cost = params["installation_cost"]
    volume_capacity = params["volume_capacity"]
    customer_demand = params["customer_demand"]
    delivery_cost_matrix = params["delivery_cost_matrix"]
    locker_coordinates_x = params["locker_coordinates_x"]
    locker_coordinates_y = params["locker_coordinates_y"]
    customer_coordinates_x = params["customer_coordinates_x"]
    customer_coordinates_y = params["customer_coordinates_y"]

    model = pyo.ConcreteModel()

    model.customers = pyo.RangeSet(0, 14)
    model.lockers = pyo.RangeSet(0, 5)

    model.installation_cost = pyo.Param(
        model.lockers,
        initialize=lambda mdl, j: installation_cost[j],
        within=pyo.NonNegativeReals,
    )
    model.volume_capacity = pyo.Param(
        model.lockers,
        initialize=lambda mdl, j: volume_capacity[j],
        within=pyo.NonNegativeReals,
    )
    model.customer_demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, i: customer_demand[i],
        within=pyo.NonNegativeReals,
    )
    model.delivery_cost_matrix = pyo.Param(
        model.customers,
        model.lockers,
        initialize=lambda mdl, i, j: delivery_cost_matrix[i][j],
        within=pyo.NonNegativeReals,
    )
    model.locker_coordinates_x = pyo.Param(
        model.lockers,
        initialize=lambda mdl, j: locker_coordinates_x[j],
        within=pyo.Reals,
    )
    model.locker_coordinates_y = pyo.Param(
        model.lockers,
        initialize=lambda mdl, j: locker_coordinates_y[j],
        within=pyo.Reals,
    )
    model.customer_coordinates_x = pyo.Param(
        model.customers,
        initialize=lambda mdl, i: customer_coordinates_x[i],
        within=pyo.Reals,
    )
    model.customer_coordinates_y = pyo.Param(
        model.customers,
        initialize=lambda mdl, i: customer_coordinates_y[i],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.lockers, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.customers, model.lockers, domain=pyo.Binary
    )

    def single_source_rule(mdl, i):
        return sum(mdl.assigned[i, j] for j in mdl.lockers) == 1

    model.single_source_constraints = pyo.Constraint(
        model.customers, rule=single_source_rule
    )

    def capacity_rule(mdl, j):
        return (
            sum(
                mdl.customer_demand[i] * mdl.assigned[i, j]
                for i in mdl.customers
            )
            <= mdl.volume_capacity[j] * mdl.opened[j]
        )

    model.capacity_constraints = pyo.Constraint(
        model.lockers, rule=capacity_rule
    )

    def activation_rule(mdl, i, j):
        return mdl.assigned[i, j] <= mdl.opened[j]

    model.activation_constraints = pyo.Constraint(
        model.customers, model.lockers, rule=activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.installation_cost[j] * model.opened[j]
                for j in model.lockers
            )
            + sum(
                model.delivery_cost_matrix[i, j] * model.assigned[i, j]
                for i in model.customers
                for j in model.lockers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Unexpected solver exceptions propagate to the calling harness.
        if not str(exc).startswith("A feasible solution was not found"):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}