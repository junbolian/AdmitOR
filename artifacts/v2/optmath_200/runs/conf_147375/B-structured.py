# IR: {"sets":{"cities":[0,1,2,3],"products":[0,1],"arcs":"ordered city pairs (i,j) with i != j","generic_entries":"lexicographically sorted (i,j,p) with (i,j) not in {(0,1),(1,0)}"},"params":["shipping_cost_per_unit","joint_capacity","product_capacity_0_0to1","product_capacity_1_0to1","product_capacity_0_1to0","product_capacity_1_1to0","product_capacity_generic_low","product_capacity_generic_high","demand_city1_product0","demand_city1_product1","demand_city2_product0","supply_city2_product1","supply_city3_product0","demand_city3_product1"],"derived":{"net_requirement":"b[0,0]=b[0,1]=0; b[1,0]=demand_city1_product0; b[1,1]=demand_city1_product1; b[2,0]=demand_city2_product0; b[2,1]=-supply_city2_product1; b[3,0]=-supply_city3_product0; b[3,1]=demand_city3_product1","capacity":"use the four named arc-product capacities; for generic entry of zero-based rank r among N entries, use low+(high-low)*r/(N-1)","capacity_convention":"Individual generic capacities are unspecified; assume deterministic linear interpolation over the supplied range."},"variables":{"x[i,j,p]":"nonnegative continuous shipment for each arc and product"},"constraints":["For each city i and product p: sum_j x[j,i,p] - sum_j x[i,j,p] = b[i,p].","For each arc (i,j): sum_p x[i,j,p] <= joint_capacity.","For each arc (i,j) and product p: x[i,j,p] <= capacity[i,j,p]."],"objective":"minimize shipping_cost_per_unit * sum_(i,j,p) x[i,j,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    shipping_cost = params["shipping_cost_per_unit"]
    joint_capacity = params["joint_capacity"]
    cap_0_0to1 = params["product_capacity_0_0to1"]
    cap_1_0to1 = params["product_capacity_1_0to1"]
    cap_0_1to0 = params["product_capacity_0_1to0"]
    cap_1_1to0 = params["product_capacity_1_1to0"]
    generic_low = params["product_capacity_generic_low"]
    generic_high = params["product_capacity_generic_high"]
    demand_1_0 = params["demand_city1_product0"]
    demand_1_1 = params["demand_city1_product1"]
    demand_2_0 = params["demand_city2_product0"]
    supply_2_1 = params["supply_city2_product1"]
    supply_3_0 = params["supply_city3_product0"]
    demand_3_1 = params["demand_city3_product1"]

    cities = tuple(range(4))
    products = tuple(range(2))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    net_requirement = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): demand_1_0,
        (1, 1): demand_1_1,
        (2, 0): demand_2_0,
        (2, 1): -supply_2_1,
        (3, 0): -supply_3_0,
        (3, 1): demand_3_1,
    }

    capacities = {
        (0, 1, 0): cap_0_0to1,
        (0, 1, 1): cap_1_0to1,
        (1, 0, 0): cap_0_1to0,
        (1, 0, 1): cap_1_1to0,
    }
    generic_entries = sorted(
        (i, j, product)
        for i, j in arcs
        for product in products
        if (i, j) not in {(0, 1), (1, 0)}
    )
    for rank, entry in enumerate(generic_entries):
        capacities[entry] = (
            generic_low
            + (generic_high - generic_low) * rank / (len(generic_entries) - 1)
        )

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.products = pyo.Set(initialize=products, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.shipment = pyo.Var(
        model.arcs, model.products, domain=pyo.NonNegativeReals
    )

    def flow_balance_rule(instance, city, product):
        incoming = sum(
            instance.shipment[other, city, product]
            for other in cities
            if other != city
        )
        outgoing = sum(
            instance.shipment[city, other, product]
            for other in cities
            if other != city
        )
        return incoming - outgoing == net_requirement[city, product]

    model.flow_balance = pyo.Constraint(
        model.cities, model.products, rule=flow_balance_rule
    )

    def joint_capacity_rule(instance, origin, destination):
        return sum(
            instance.shipment[origin, destination, product]
            for product in products
        ) <= joint_capacity

    model.joint_capacity_limit = pyo.Constraint(
        model.arcs, rule=joint_capacity_rule
    )

    def product_capacity_rule(instance, origin, destination, product):
        return (
            instance.shipment[origin, destination, product]
            <= capacities[origin, destination, product]
        )

    model.product_capacity_limit = pyo.Constraint(
        model.arcs, model.products, rule=product_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=shipping_cost
        * sum(
            model.shipment[i, j, product]
            for i, j in arcs
            for product in products
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}