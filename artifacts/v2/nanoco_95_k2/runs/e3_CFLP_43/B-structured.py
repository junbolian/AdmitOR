# IR: {"sets":{"I":"range(params['num_customers'])","J":"range(params['num_lockers'])"},"params":{"num_lockers":"number of locker sites","num_customers":"number of customers","locker_fixed_costs[j]":"fixed activation cost","locker_capacities[j]":"parcel capacity","customer_demands[i]":"parcel demand","delivery_cost_matrix[i][j]":"customer-to-locker assignment cost"},"variables":{"x[i,j]":"Binary: customer i assigned to locker j","y[j]":"Binary: locker j activated"},"constraints":["sum(j in J, x[i,j]) == 1 for each i in I","sum(i in I, customer_demands[i]*x[i,j]) <= locker_capacities[j]*y[j] for each j in J","x[i,j] <= y[j] for each (i,j) in I x J"],"objective":"minimize sum(j in J, locker_fixed_costs[j]*y[j]) + sum((i,j) in I x J, delivery_cost_matrix[i][j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.customers = pyo.Set(
        initialize=range(params["num_customers"]), ordered=True
    )
    model.lockers = pyo.Set(
        initialize=range(params["num_lockers"]), ordered=True
    )

    model.fixed_cost = pyo.Param(
        model.lockers,
        initialize=lambda mdl, j: params["locker_fixed_costs"][j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.lockers,
        initialize=lambda mdl, j: params["locker_capacities"][j],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, i: params["customer_demands"][i],
        within=pyo.NonNegativeReals,
    )
    model.delivery_cost = pyo.Param(
        model.customers,
        model.lockers,
        initialize=lambda mdl, i, j: params["delivery_cost_matrix"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.customers, model.lockers, domain=pyo.Binary)
    model.y = pyo.Var(model.lockers, domain=pyo.Binary)

    model.single_sourcing = pyo.Constraint(
        model.customers,
        rule=lambda mdl, i: pyo.quicksum(
            mdl.x[i, j] for j in mdl.lockers
        ) == 1,
    )
    model.capacity_limit = pyo.Constraint(
        model.lockers,
        rule=lambda mdl, j: pyo.quicksum(
            mdl.demand[i] * mdl.x[i, j] for i in mdl.customers
        ) <= mdl.capacity[j] * mdl.y[j],
    )
    model.activation_link = pyo.Constraint(
        model.customers,
        model.lockers,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.y[j],
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.fixed_cost[j] * model.y[j] for j in model.lockers
        )
        + pyo.quicksum(
            model.delivery_cost[i, j] * model.x[i, j]
            for i in model.customers
            for j in model.lockers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An unsuccessful solve can raise before loading a solution.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}