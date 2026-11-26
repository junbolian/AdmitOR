# IR: {"sets":{"C":"{1,...,20}","V":"{0,...,21}; 0=start depot, 21=return depot","A":"({0}xC) union {(i,j) in CxC:i!=j} union (Cx{21})"},"params":{"depot_x":"params['depot_x']","depot_y":"params['depot_y']","depot_tw_start":"params['depot_tw_start']","depot_tw_end":"params['depot_tw_end']","vehicle_count_max":"params['vehicle_count_max']","vehicle_capacity":"params['vehicle_capacity']","customer_x":"params['customer_x'] indexed by C","customer_y":"params['customer_y'] indexed by C","demand":"params['demand'] indexed by C","tw_early":"params['tw_early'] indexed by C","tw_late":"params['tw_late'] indexed by C","service_time":"params['service_time'] indexed by C, or a common scalar","distance":"Euclidean distance; travel time equals distance","M_start[j]":"max(0,depot_tw_start+distance[0,j]-tw_early[j])","M_customer[i,j]":"max(0,tw_late[i]+service_time[i]+distance[i,j]-tw_early[j])","M_return[i]":"max(0,tw_late[i]+service_time[i]+distance[i,21]-depot_tw_end)"},"variables":{"x[i,j]":"binary for (i,j) in A; selected arc","f[i,j]":"nonnegative continuous for (i,j) in A; undelivered load carried on arc","t[i]":"continuous in [tw_early[i],tw_late[i]] for i in C; service start","u[i]":"continuous in [1,20] for i in C; route position"},"constraints":["For each customer j: sum_i x[i,j]=1.","For each customer i: sum_j x[i,j]=1.","sum_j x[0,j]=sum_i x[i,21].","sum_j x[0,j]<=vehicle_count_max.","For each arc (i,j): f[i,j]<=vehicle_capacity*x[i,j].","For each customer i: sum_h f[h,i]-sum_j f[i,j]=demand[i].","For each customer i: f[i,21]=0.","For each customer j: t[j]>=depot_tw_start+distance[0,j]-M_start[j]*(1-x[0,j]).","For distinct customers i,j: t[j]>=t[i]+service_time[i]+distance[i,j]-M_customer[i,j]*(1-x[i,j]).","For each customer i: t[i]+service_time[i]+distance[i,21]<=depot_tw_end+M_return[i]*(1-x[i,21]).","For distinct customers i,j: u[j]>=u[i]+1-20*(1-x[i,j])."],"objective":"minimize sum_(i,j) in A distance[i,j]*x[i,j]"}
#
# Input convention: customer data may be length-20 sequences in customer-ID
# order or mappings keyed by customer IDs (integers or their string forms).
# service_time may additionally be a scalar shared by all customers.
# Travel time equals Euclidean distance in the supplied time units.
# Waiting is permitted by the service-start inequalities.
# Position constraints exclude disconnected cycles even with zero demand,
# zero travel distance, or zero service duration.

from collections.abc import Mapping
from math import hypot
from numbers import Real

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    customers = tuple(range(1, 21))
    start_depot = 0
    return_depot = 21
    customer_count = len(customers)

    depot_x = float(params["depot_x"])
    depot_y = float(params["depot_y"])
    depot_tw_start = float(params["depot_tw_start"])
    depot_tw_end = float(params["depot_tw_end"])
    vehicle_count_max = params["vehicle_count_max"]
    vehicle_capacity = float(params["vehicle_capacity"])

    def read_customer_data(parameter_name, allow_scalar=False):
        raw = params[parameter_name]
        if allow_scalar and isinstance(raw, Real):
            return {customer: float(raw) for customer in customers}
        if isinstance(raw, Mapping):
            return {
                customer: float(
                    raw[customer] if customer in raw else raw[str(customer)]
                )
                for customer in customers
            }
        return {
            customer: float(raw[customer - 1])
            for customer in customers
        }

    customer_x = read_customer_data("customer_x")
    customer_y = read_customer_data("customer_y")
    demand = read_customer_data("demand")
    tw_early = read_customer_data("tw_early")
    tw_late = read_customer_data("tw_late")
    service_time = read_customer_data("service_time", allow_scalar=True)

    coordinates = {
        start_depot: (depot_x, depot_y),
        return_depot: (depot_x, depot_y),
        **{
            customer: (customer_x[customer], customer_y[customer])
            for customer in customers
        },
    }

    customer_arcs = tuple(
        (origin, destination)
        for origin in customers
        for destination in customers
        if origin != destination
    )
    arcs = (
        tuple((start_depot, customer) for customer in customers)
        + customer_arcs
        + tuple((customer, return_depot) for customer in customers)
    )

    distances = {
        (origin, destination): hypot(
            coordinates[origin][0] - coordinates[destination][0],
            coordinates[origin][1] - coordinates[destination][1],
        )
        for origin, destination in arcs
    }

    incoming = {
        customer: tuple(
            origin for origin, destination in arcs
            if destination == customer
        )
        for customer in customers
    }
    outgoing = {
        customer: tuple(
            destination for origin, destination in arcs
            if origin == customer
        )
        for customer in customers
    }

    start_big_m = {
        customer: max(
            0.0,
            depot_tw_start
            + distances[start_depot, customer]
            - tw_early[customer],
        )
        for customer in customers
    }
    customer_big_m = {
        (origin, destination): max(
            0.0,
            tw_late[origin]
            + service_time[origin]
            + distances[origin, destination]
            - tw_early[destination],
        )
        for origin, destination in customer_arcs
    }
    return_big_m = {
        customer: max(
            0.0,
            tw_late[customer]
            + service_time[customer]
            + distances[customer, return_depot]
            - depot_tw_end,
        )
        for customer in customers
    }

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=customers, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.CA = pyo.Set(dimen=2, initialize=customer_arcs, ordered=True)

    model.fleet_limit = pyo.Param(
        initialize=vehicle_count_max,
        within=pyo.NonNegativeIntegers,
    )
    model.truck_capacity = pyo.Param(
        initialize=vehicle_capacity,
        within=pyo.NonNegativeReals,
    )
    model.customer_demand = pyo.Param(
        model.C,
        initialize=demand,
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.t = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=lambda mdl, customer: (
            tw_early[customer],
            tw_late[customer],
        ),
    )
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    def visit_in_rule(mdl, customer):
        return sum(
            mdl.x[origin, customer] for origin in incoming[customer]
        ) == 1

    model.visit_in = pyo.Constraint(model.C, rule=visit_in_rule)

    def visit_out_rule(mdl, customer):
        return sum(
            mdl.x[customer, destination]
            for destination in outgoing[customer]
        ) == 1

    model.visit_out = pyo.Constraint(model.C, rule=visit_out_rule)

    model.depot_balance = pyo.Constraint(
        expr=sum(model.x[start_depot, customer] for customer in model.C)
        == sum(model.x[customer, return_depot] for customer in model.C)
    )

    model.fleet_capacity = pyo.Constraint(
        expr=sum(model.x[start_depot, customer] for customer in model.C)
        <= model.fleet_limit
    )

    def arc_capacity_rule(mdl, origin, destination):
        return (
            mdl.f[origin, destination]
            <= mdl.truck_capacity * mdl.x[origin, destination]
        )

    model.arc_capacity = pyo.Constraint(model.A, rule=arc_capacity_rule)

    def delivery_balance_rule(mdl, customer):
        return (
            sum(
                mdl.f[origin, customer]
                for origin in incoming[customer]
            )
            - sum(
                mdl.f[customer, destination]
                for destination in outgoing[customer]
            )
            == mdl.customer_demand[customer]
        )

    model.delivery_balance = pyo.Constraint(
        model.C, rule=delivery_balance_rule
    )

    model.empty_return = pyo.Constraint(
        model.C,
        rule=lambda mdl, customer: mdl.f[customer, return_depot] == 0,
    )

    def departure_time_rule(mdl, customer):
        return (
            mdl.t[customer]
            >= depot_tw_start
            + distances[start_depot, customer]
            - start_big_m[customer] * (1 - mdl.x[start_depot, customer])
        )

    model.departure_time = pyo.Constraint(
        model.C, rule=departure_time_rule
    )

    def customer_time_rule(mdl, origin, destination):
        return (
            mdl.t[destination]
            >= mdl.t[origin]
            + service_time[origin]
            + distances[origin, destination]
            - customer_big_m[origin, destination]
            * (1 - mdl.x[origin, destination])
        )

    model.customer_time = pyo.Constraint(
        model.CA, rule=customer_time_rule
    )

    def return_time_rule(mdl, customer):
        return (
            mdl.t[customer]
            + service_time[customer]
            + distances[customer, return_depot]
            <= depot_tw_end
            + return_big_m[customer]
            * (1 - mdl.x[customer, return_depot])
        )

    model.return_time = pyo.Constraint(model.C, rule=return_time_rule)

    def route_order_rule(mdl, origin, destination):
        return (
            mdl.u[destination]
            >= mdl.u[origin]
            + 1
            - customer_count * (1 - mdl.x[origin, destination])
        )

    model.route_order = pyo.Constraint(model.CA, rule=route_order_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            distances[origin, destination] * model.x[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}