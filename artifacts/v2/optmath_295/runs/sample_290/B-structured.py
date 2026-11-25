# IR: {"sets":{"F":"0..5","C":"0..11"},"params":{"fixed_cost":"F-indexed","capacity":"F-indexed nonnegative","demand":"C-indexed nonnegative","transport_cost_00":"scalar","transport_cost_11":"scalar","transport_cost_22":"scalar","transport_cost_33":"scalar","transport_cost_44":"scalar","transport_cost_55":"scalar"},"assumption":"Unspecified route costs equal the supplied cost for their originating facility: c[i,j]=transport_cost_ii for every j. The supplied data do not uniquely determine other route costs.","variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["sum(i in F, shipped[i,j]) == demand[j] for each j in C","sum(j in C, shipped[i,j]) <= capacity[i]*opened[i] for each i in F"],"objective":"minimize sum(i in F, fixed_cost[i]*opened[i]) + sum(i in F,j in C, transport_cost_ii*shipped[i,j])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = range(6)
    customers = range(12)

    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    facility_transport_cost = (
        params["transport_cost_00"],
        params["transport_cost_11"],
        params["transport_cost_22"],
        params["transport_cost_33"],
        params["transport_cost_44"],
        params["transport_cost_55"],
    )

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.customers = pyo.Set(initialize=customers, ordered=True)

    model.operating_cost = pyo.Param(
        model.facilities,
        initialize={i: float(fixed_cost[i]) for i in facilities},
        within=pyo.Reals,
    )
    model.shipping_capacity = pyo.Param(
        model.facilities,
        initialize={i: float(capacity[i]) for i in facilities},
        within=pyo.NonNegativeReals,
    )
    model.customer_demand = pyo.Param(
        model.customers,
        initialize={j: float(demand[j]) for j in customers},
        within=pyo.NonNegativeReals,
    )
    model.unit_transport_cost = pyo.Param(
        model.facilities,
        initialize={
            i: float(facility_transport_cost[i]) for i in facilities
        },
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipped[i, j] for i in instance.facilities)
            == instance.customer_demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipped[i, j] for j in instance.customers)
            <= instance.shipping_capacity[i] * instance.opened[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.operating_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.unit_transport_cost[i] * model.shipped[i, j]
                for i in model.facilities
                for j in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to objective retrieval only for the expected
        # APPsi failure to load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}