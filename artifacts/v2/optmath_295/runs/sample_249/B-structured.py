# IR: {"sets":{"C":[0,1,2,3],"P":[0,1],"A":"{(i,j) in C x C: i != j}"},"params":{"cost":"params['transport_cost']","joint_cap":"params['joint_capacity']","cap[p,i,j]":"params[f'product{p}_capacity_{i}{j}']","supply[i,p]":"params[f'net_flow_{i}_product{p}']"},"variables":{"x[p,i,j]":"NonNegativeReals, indexed by P x A"},"constraints":["For each (i,p): sum(j != i, x[p,i,j]) - sum(j != i, x[p,j,i]) == supply[i,p]","For each (i,j) in A: sum(p in P, x[p,i,j]) <= joint_cap","For each p in P and (i,j) in A: x[p,i,j] <= cap[p,i,j]"],"objective":"Minimize cost * sum(p in P, (i,j) in A, x[p,i,j])"}

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

    model.transport_rate = pyo.Param(
        initialize=params["transport_cost"],
        within=pyo.Reals,
    )
    model.joint_limit = pyo.Param(
        initialize=params["joint_capacity"],
        within=pyo.Reals,
    )
    model.product_limits = pyo.Param(
        model.products,
        model.arcs,
        initialize={
            (product, origin, destination): params[
                f"product{product}_capacity_{origin}{destination}"
            ]
            for product in model.products
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )
    model.net_supplies = pyo.Param(
        model.cities,
        model.products,
        initialize={
            (city, product): params[f"net_flow_{city}_product{product}"]
            for city in model.cities
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.shipments = pyo.Var(
        model.products,
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def flow_balance_rule(mdl, city, product):
        outflow = sum(
            mdl.shipments[product, city, other]
            for other in mdl.cities
            if other != city
        )
        inflow = sum(
            mdl.shipments[product, other, city]
            for other in mdl.cities
            if other != city
        )
        return outflow - inflow == mdl.net_supplies[city, product]

    model.flow_balance = pyo.Constraint(
        model.cities,
        model.products,
        rule=flow_balance_rule,
    )

    def joint_capacity_rule(mdl, origin, destination):
        return (
            sum(
                mdl.shipments[product, origin, destination]
                for product in mdl.products
            )
            <= mdl.joint_limit
        )

    model.joint_capacity_constraints = pyo.Constraint(
        model.arcs,
        rule=joint_capacity_rule,
    )

    def product_capacity_rule(mdl, product, origin, destination):
        return (
            mdl.shipments[product, origin, destination]
            <= mdl.product_limits[product, origin, destination]
        )

    model.product_capacity_constraints = pyo.Constraint(
        model.products,
        model.arcs,
        rule=product_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=model.transport_rate
        * sum(
            model.shipments[product, origin, destination]
            for product in model.products
            for origin, destination in model.arcs
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