# IR: {"sets":{"C":[0,1,2,3],"P":[0,1],"A":"{(i,j) in C x C: i != j}"},"params":{"cost":"params['transport_cost_per_unit']","joint_capacity":"params['joint_capacity_per_pair']","net_supply[c,p]":"params[f'net_flow_city{c}_product{p}']","capacity[i,j,p]":"params[f'product{p}_capacity_city{i}_city{j}']"},"variables":{"flow[i,j,p]":"continuous nonnegative, indexed by A x P"},"constraints":["For each c,p: sum(flow[c,j,p] for j != c) - sum(flow[i,c,p] for i != c) = net_supply[c,p].","For each (i,j) in A: sum(flow[i,j,p] for p in P) <= joint_capacity.","For each (i,j),p: flow[i,j,p] <= capacity[i,j,p]."],"objective":"minimize cost * sum(flow[i,j,p] for (i,j) in A, p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(4), ordered=True)
    model.products = pyo.Set(initialize=range(2), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
        ordered=True,
    )

    model.transport_cost = pyo.Param(
        initialize=params["transport_cost_per_unit"],
        within=pyo.Reals,
    )
    model.joint_capacity = pyo.Param(
        initialize=params["joint_capacity_per_pair"],
        within=pyo.Reals,
    )
    model.net_supply = pyo.Param(
        model.cities,
        model.products,
        initialize={
            (city, product): params[f"net_flow_city{city}_product{product}"]
            for city in model.cities
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.product_capacity = pyo.Param(
        model.arcs,
        model.products,
        initialize={
            (origin, destination, product): params[
                f"product{product}_capacity_city{origin}_city{destination}"
            ]
            for origin, destination in model.arcs
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(
        model.arcs,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def flow_balance_rule(network, city, product):
        outgoing = sum(
            network.flow[city, destination, product]
            for destination in network.cities
            if destination != city
        )
        incoming = sum(
            network.flow[origin, city, product]
            for origin in network.cities
            if origin != city
        )
        return outgoing - incoming == network.net_supply[city, product]

    model.flow_balance = pyo.Constraint(
        model.cities,
        model.products,
        rule=flow_balance_rule,
    )

    def joint_capacity_rule(network, origin, destination):
        return (
            sum(
                network.flow[origin, destination, product]
                for product in network.products
            )
            <= network.joint_capacity
        )

    model.joint_capacity_limits = pyo.Constraint(
        model.arcs,
        rule=joint_capacity_rule,
    )

    def product_capacity_rule(network, origin, destination, product):
        return (
            network.flow[origin, destination, product]
            <= network.product_capacity[origin, destination, product]
        )

    model.product_capacity_limits = pyo.Constraint(
        model.arcs,
        model.products,
        rule=product_capacity_rule,
    )

    model.total_transport_cost = pyo.Objective(
        expr=model.transport_cost
        * sum(
            model.flow[origin, destination, product]
            for origin, destination in model.arcs
            for product in model.products
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_transport_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}