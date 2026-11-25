# IR: {"sets":{"C":[0,1,2],"P":[0,1],"A":"{(i,j) in C x C: i != j}"},"params":["shipping_cost","net_demand_prod0_city0","net_supply_prod1_city0","net_demand_prod0_city1","net_demand_prod1_city1","net_supply_prod0_city2","net_demand_prod1_city2","joint_capacity","prod_cap_01_p0","prod_cap_01_p1","prod_cap_02_p0","prod_cap_02_p1","prod_cap_10_p0","prod_cap_10_p1","prod_cap_12_p0","prod_cap_12_p1","prod_cap_20_p0","prod_cap_20_p1","prod_cap_21_p0","prod_cap_21_p1"],"derived":{"b[c,p]":{"0,0":"net_demand_prod0_city0","0,1":"-net_supply_prod1_city0","1,0":"net_demand_prod0_city1","1,1":"net_demand_prod1_city1","2,0":"-net_supply_prod0_city2","2,1":"net_demand_prod1_city2"},"u[i,j,p]":"prod_cap_{i}{j}_p{p}"},"variables":{"x[i,j,p]":"continuous nonnegative, (i,j) in A, p in P"},"constraints":["For each c in C and p in P: sum(x[i,c,p] for i != c) - sum(x[c,j,p] for j != c) = b[c,p]","For each (i,j) in A: sum(x[i,j,p] for p in P) <= joint_capacity","For each (i,j) in A and p in P: x[i,j,p] <= u[i,j,p]"],"objective":"minimize shipping_cost * sum(x[i,j,p] for (i,j) in A and p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.products = pyo.Set(initialize=[0, 1], ordered=True)
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

    model.shipping_cost = pyo.Param(
        initialize=params["shipping_cost"]
    )
    model.joint_capacity = pyo.Param(
        initialize=params["joint_capacity"]
    )

    model.net_requirement = pyo.Param(
        model.cities,
        model.products,
        initialize={
            (0, 0): params["net_demand_prod0_city0"],
            (0, 1): -params["net_supply_prod1_city0"],
            (1, 0): params["net_demand_prod0_city1"],
            (1, 1): params["net_demand_prod1_city1"],
            (2, 0): -params["net_supply_prod0_city2"],
            (2, 1): params["net_demand_prod1_city2"],
        },
    )

    model.product_capacity = pyo.Param(
        model.arcs,
        model.products,
        initialize={
            (0, 1, 0): params["prod_cap_01_p0"],
            (0, 1, 1): params["prod_cap_01_p1"],
            (0, 2, 0): params["prod_cap_02_p0"],
            (0, 2, 1): params["prod_cap_02_p1"],
            (1, 0, 0): params["prod_cap_10_p0"],
            (1, 0, 1): params["prod_cap_10_p1"],
            (1, 2, 0): params["prod_cap_12_p0"],
            (1, 2, 1): params["prod_cap_12_p1"],
            (2, 0, 0): params["prod_cap_20_p0"],
            (2, 0, 1): params["prod_cap_20_p1"],
            (2, 1, 0): params["prod_cap_21_p0"],
            (2, 1, 1): params["prod_cap_21_p1"],
        },
    )

    model.shipment = pyo.Var(
        model.arcs,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def flow_balance_rule(network, city, product):
        inflow = sum(
            network.shipment[origin, city, product]
            for origin in network.cities
            if origin != city
        )
        outflow = sum(
            network.shipment[city, destination, product]
            for destination in network.cities
            if destination != city
        )
        return inflow - outflow == network.net_requirement[city, product]

    model.flow_balance = pyo.Constraint(
        model.cities,
        model.products,
        rule=flow_balance_rule,
    )

    def joint_capacity_rule(network, origin, destination):
        return (
            sum(
                network.shipment[origin, destination, product]
                for product in network.products
            )
            <= network.joint_capacity
        )

    model.joint_capacity_limit = pyo.Constraint(
        model.arcs,
        rule=joint_capacity_rule,
    )

    def product_capacity_rule(network, origin, destination, product):
        return (
            network.shipment[origin, destination, product]
            <= network.product_capacity[origin, destination, product]
        )

    model.product_capacity_limit = pyo.Constraint(
        model.arcs,
        model.products,
        rule=product_capacity_rule,
    )

    model.total_shipping_cost = pyo.Objective(
        expr=model.shipping_cost
        * sum(
            model.shipment[origin, destination, product]
            for origin, destination in model.arcs
            for product in model.products
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_shipping_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}