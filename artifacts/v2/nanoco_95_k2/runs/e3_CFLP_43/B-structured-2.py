# IR: {"sets":{"I":"range(params['num_customers'])","J":"range(params['num_lockers'])"},"params":{"num_customers":"customer count","num_lockers":"locker count","locker_fixed_costs[j]":"fixed activation cost","locker_capacities[j]":"parcel capacity","customer_demands[i]":"parcel demand","delivery_cost_matrix[i,j]":"cost of assigning customer i to locker j"},"variables":{"y[j]":"Binary; locker activated","x[i,j]":"Binary; customer assigned to locker"},"constraints":["sum(j in J, x[i,j]) == 1 for each i in I","sum(i in I, customer_demands[i]*x[i,j]) <= locker_capacities[j]*y[j] for each j in J","x[i,j] <= y[j] for each (i,j) in I x J"],"objective":"minimize sum(j in J, locker_fixed_costs[j]*y[j]) + sum(i in I,j in J, delivery_cost_matrix[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_customers = params["num_customers"]
    num_lockers = params["num_lockers"]
    locker_fixed_costs = params["locker_fixed_costs"]
    locker_capacities = params["locker_capacities"]
    customer_demands = params["customer_demands"]
    delivery_cost_matrix = params["delivery_cost_matrix"]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(num_customers), ordered=True)
    model.J = pyo.Set(initialize=range(num_lockers), ordered=True)

    model.fixed_cost = pyo.Param(
        model.J,
        initialize=lambda mdl, j: locker_fixed_costs[j],
    )
    model.capacity = pyo.Param(
        model.J,
        initialize=lambda mdl, j: locker_capacities[j],
    )
    model.demand = pyo.Param(
        model.I,
        initialize=lambda mdl, i: customer_demands[i],
    )
    model.delivery_cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: delivery_cost_matrix[i][j],
    )

    model.y = pyo.Var(model.J, domain=pyo.Binary)
    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def single_source_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == 1

    model.single_source = pyo.Constraint(
        model.I, rule=single_source_rule
    )

    def capacity_rule(mdl, j):
        return (
            sum(mdl.demand[i] * mdl.x[i, j] for i in mdl.I)
            <= mdl.capacity[j] * mdl.y[j]
        )

    model.capacity_limit = pyo.Constraint(
        model.J, rule=capacity_rule
    )

    def activation_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.y[j]

    model.activation_link = pyo.Constraint(
        model.I, model.J, rule=activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[j] * model.y[j] for j in model.J)
            + sum(
                model.delivery_cost[i, j] * model.x[i, j]
                for i in model.I
                for j in model.J
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}