import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Sets
    model.COMMODITIES = pyo.Set(initialize=[1, 2])
    model.LOCATIONS = pyo.Set(initialize=[0, 1, 2, 3])

    # Routes that have facility installation parameters
    facility_routes = [(0, 3), (1, 2), (1, 3), (2, 0), (2, 1), (3, 1), (3, 2)]
    model.FACILITY_ROUTES = pyo.Set(initialize=facility_routes, dimen=2)

    # Commodity-specific routes
    # Commodity 1: 0->3, 0->1, 0->2
    # Commodity 2: 1->2, 1->3
    c1_routes = [(0, 3), (0, 1), (0, 2)]
    c2_routes = [(1, 2), (1, 3)]

    # Transportation costs dictionary
    transport_cost = {}
    # Commodity 1
    transport_cost[(1, 0, 3)] = params["transport_cost_c1_0_3"]
    transport_cost[(1, 0, 1)] = params["transport_cost_c1_0_1"]
    transport_cost[(1, 0, 2)] = params["transport_cost_c1_0_2"]
    # Commodity 2
    transport_cost[(2, 1, 2)] = params["transport_cost_c2_1_2"]
    transport_cost[(2, 1, 3)] = params["transport_cost_c2_1_3"]

    # Installation costs and capacities dictionary
    install_cost = {}
    capacity = {}
    install_cost[(0, 3)] = params["install_cost_0_3"]
    capacity[(0, 3)] = params["capacity_0_3"]
    install_cost[(1, 2)] = params["install_cost_1_2"]
    capacity[(1, 2)] = params["capacity_1_2"]
    install_cost[(1, 3)] = params["install_cost_1_3"]
    capacity[(1, 3)] = params["capacity_1_3"]
    install_cost[(2, 0)] = params["install_cost_2_0"]
    capacity[(2, 0)] = params["capacity_2_0"]
    install_cost[(2, 1)] = params["install_cost_2_1"]
    capacity[(2, 1)] = params["capacity_2_1"]
    install_cost[(3, 1)] = params["install_cost_3_1"]
    capacity[(3, 1)] = params["capacity_3_1"]
    install_cost[(3, 2)] = params["install_cost_3_2"]
    capacity[(3, 2)] = params["capacity_3_2"]

    # Decision Variables
    # Flow variables for each commodity on its routes, bounded 0 to 1
    def flow_c1_bounds(model, i, j):
        return (0, 1)
    def flow_c2_bounds(model, i, j):
        return (0, 1)

    model.FLOW_C1_ROUTES = pyo.Set(initialize=c1_routes, dimen=2)
    model.FLOW_C2_ROUTES = pyo.Set(initialize=c2_routes, dimen=2)

    model.flow_c1 = pyo.Var(model.FLOW_C1_ROUTES, domain=pyo.NonNegativeReals, bounds=(0, 1))
    model.flow_c2 = pyo.Var(model.FLOW_C2_ROUTES, domain=pyo.NonNegativeReals, bounds=(0, 1))

    # Integer facilities installed on each facility route
    model.facilities = pyo.Var(model.FACILITY_ROUTES, domain=pyo.NonNegativeIntegers)


    def flow_c1_dict_rule(model, i, j):
        return model.flow_c1[i, j]
    # We use the variable objects directly.

    # Objective:
    # Transportation cost for commodity 1 on its routes
    # Transportation cost for commodity 2 on its routes
    # Installation cost for facilities on all facility routes
    def obj_rule(model):
        trans_c1 = sum(
            transport_cost[(1, i, j)] * model.flow_c1[i, j] for (i, j) in c1_routes
        )
        trans_c2 = sum(
            transport_cost[(2, i, j)] * model.flow_c2[i, j] for (i, j) in c2_routes
        )
        install = sum(
            install_cost[(i, j)] * model.facilities[i, j] for (i, j) in facility_routes
        )
        return trans_c1 + trans_c2 + install

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Capacity constraints:
    # On the shared route 0->3: flow_c1[0,3] + 0 (no commodity 2 on 0->3) <= capacity_0_3 * facilities[0,3]
    # Actually, the problem says "combined flow of Commodity 1 and Commodity 2 on the route from Location 0 to Location 3 must not exceed 607 * facilities".
    # Commodity 2 does not use route 0->3, so only flow_c1[0,3] contributes.
    def cap_0_3_rule(model):
        return model.flow_c1[0, 3] <= capacity[(0, 3)] * model.facilities[0, 3]
    model.cap_0_3 = pyo.Constraint(rule=cap_0_3_rule)

    # On route 1->2: commodity 2 flows. Also maybe commodity 1? Commodity 1 has routes 0->3, 0->1, 0->2, not 1->2. So only commodity 2.
    def cap_1_2_rule(model):
        return model.flow_c2[1, 2] <= capacity[(1, 2)] * model.facilities[1, 2]
    model.cap_1_2 = pyo.Constraint(rule=cap_1_2_rule)

    # On route 1->3: commodity 2 flows.
    def cap_1_3_rule(model):
        return model.flow_c2[1, 3] <= capacity[(1, 3)] * model.facilities[1, 3]
    model.cap_1_3 = pyo.Constraint(rule=cap_1_3_rule)

    # On route 2->0: no commodity flows defined (commodity 1 does not use it, commodity 2 does not use it).
    # But facility may be installed. Since no flow, the capacity constraint is 0 <= capacity * facilities, which is always true.
    # We omit it since no flow uses it.

    # On route 2->1: no commodity flows defined.
    # Omit.

    # On route 3->1: no commodity flows defined.
    # Omit.

    # On route 3->2: no commodity flows defined.
    # Omit.

    # Flow conservation constraints:

    # Commodity 1: originates at location 0, destination at location 3.
    # At location 0: total flow out - total flow in = 1 (supply)
    # At location 3: total flow in - total flow out = 1 (demand)
    # At other locations: flow in = flow out.

    # Commodity 1 routes: (0,3), (0,1), (0,2)
    # At location 0: outflow = flow_c1[0,3] + flow_c1[0,1] + flow_c1[0,2], inflow = 0 (no incoming routes for commodity 1)
    # So outflow - inflow = 1 -> flow_c1[0,3] + flow_c1[0,1] + flow_c1[0,2] = 1

    def c1_balance_0_rule(model):
        return model.flow_c1[0, 3] + model.flow_c1[0, 1] + model.flow_c1[0, 2] == 1
    model.c1_balance_0 = pyo.Constraint(rule=c1_balance_0_rule)

    # At location 3: inflow = flow_c1[0,3], outflow = 0 (no outgoing routes for commodity 1)
    # inflow - outflow = 1 -> flow_c1[0,3] = 1

    def c1_balance_3_rule(model):
        return model.flow_c1[0, 3] == 1
    model.c1_balance_3 = pyo.Constraint(rule=c1_balance_3_rule)

    # At location 1: inflow = flow_c1[0,1], outflow = 0 (no outgoing routes for commodity 1)
    # Since location 1 is not origin or destination for commodity 1, inflow = outflow -> flow_c1[0,1] = 0

    def c1_balance_1_rule(model):
        return model.flow_c1[0, 1] == 0
    model.c1_balance_1 = pyo.Constraint(rule=c1_balance_1_rule)

    # At location 2: inflow = flow_c1[0,2], outflow = 0
    # Since location 2 is not origin or destination for commodity 1, inflow = outflow -> flow_c1[0,2] = 0

    def c1_balance_2_rule(model):
        return model.flow_c1[0, 2] == 0
    model.c1_balance_2 = pyo.Constraint(rule=c1_balance_2_rule)

    # Commodity 2: originates at location 1, destination at location 2.
    # Routes: (1,2), (1,3)

    # At location 1: outflow = flow_c2[1,2] + flow_c2[1,3], inflow = 0 (no incoming routes for commodity 2)
    # But the problem says "At Location 1, the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # This is a bit ambiguous. "flow of Commodity 2 into Location 2" refers to flow_c2[1,2] (route 1->2).
    # "flow out of Location 3" likely refers to flow_c2[1,3] (route 1->3)?? No, flow out of Location 3 would be a route from 3 to somewhere.
    # But commodity 2 has no route from 3. The only route involving 3 for commodity 2 is 1->3 (into location 3).
    # So "flow out of Location 3" might be a misinterpretation. Perhaps it means flow_c2[1,3]?? No.
    # Let's re-read: "At Location 1, the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # This is confusing. Possibly it means: inflow at location 1 (from origin) equals outflow? Or it's a supply constraint?
    # Actually, the origin is location 1. The supply is 1 unit. So outflow - inflow = 1.
    # Outflow = flow_c2[1,2] + flow_c2[1,3]. Inflow = 0. So flow_c2[1,2] + flow_c2[1,3] = 1.
    # The statement "flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit" might be a garbled version of the conservation constraint.
    # Let's interpret: At location 1, supply = 1: flow_c2[1,2] + flow_c2[1,3] = 1.
    # At location 2: demand = 1: inflow = flow_c2[1,2] = 1.
    # At location 3: no demand, so inflow = flow_c2[1,3] = 0 (since not destination).
    # But that would force flow_c2[1,2] = 1 and flow_c2[1,3] = 0.
    # Let's check the statement: "the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # If "flow out of Location 3" refers to flow_c2[1,3] (which is into Location 3, not out), then flow_c2[1,2] - flow_c2[1,3] = 1.
    # Combined with flow_c2[1,2] + flow_c2[1,3] = 1, we get flow_c2[1,2] = 1, flow_c2[1,3] = 0.
    # That is consistent with the conservation constraints if location 3 is not a destination.
    # However, the statement says "flow out of Location 3", which is odd.
    # Let's just implement flow conservation with supply/demand:
    # At location 1 (origin): outflow - inflow = 1 -> flow_c2[1,2] + flow_c2[1,3] = 1
    # At location 2 (destination): inflow - outflow = 1 -> flow_c2[1,2] = 1
    # At location 3 (neither): inflow = outflow -> flow_c2[1,3] = 0 (since no outflow from 3)
    # This yields flow_c2[1,2] = 1, flow_c2[1,3] = 0.
    # Let's double-check: "the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # If flow_c2[1,2] - flow_c2[1,3] = 1, and flow_c2[1,2] + flow_c2[1,3] = 1, then indeed flow_c2[1,2] = 1, flow_c2[1,3] = 0.
    # So we'll use the conservation constraints as above, which are equivalent.

    def c2_balance_1_rule(model):
        return model.flow_c2[1, 2] + model.flow_c2[1, 3] == 1
    model.c2_balance_1 = pyo.Constraint(rule=c2_balance_1_rule)

    def c2_balance_2_rule(model):
        return model.flow_c2[1, 2] == 1
    model.c2_balance_2 = pyo.Constraint(rule=c2_balance_2_rule)

    def c2_balance_3_rule(model):
        return model.flow_c2[1, 3] == 0
    model.c2_balance_3 = pyo.Constraint(rule=c2_balance_3_rule)

    # Also need balance at location 0 for commodity 2? No routes for commodity 2 at location 0.
    # Not needed.

    # Solve
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as e:
        return {"objective": None, "status": str(e)[:50]}