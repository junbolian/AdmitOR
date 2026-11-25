def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    cost_matrix = params["cost_matrix"]
    max_turbines_per_feeder = params["max_turbines_per_feeder"]
    num_nodes = params["num_nodes"]
    num_turbines = params["num_turbines"]

    nodes = list(range(num_nodes))
    turbines = list(range(1, num_nodes))

    # Directed arc set: every unordered pair {i,j}, i != j, as directed arcs i->j
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cost(i, j):
        return float(cost_matrix[i][j])

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    # f[i,j]: flow of turbines carried on arc i->j (rooted tree arborescence flow)
    model.f = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    # Exactly one incoming arc to each turbine (radial: each turbine has one parent)
    def one_parent_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1
    model.one_parent = pyo.Constraint(turbines, rule=one_parent_rule)

    # No incoming arc to the root
    def root_no_in_rule(mdl):
        return sum(mdl.x[i, 0] for i in nodes if i != 0) == 0
    model.root_no_in = pyo.Constraint(rule=root_no_in_rule)

    # Flow conservation linking flow to connectivity and capacity
    # For turbine j: inflow - outflow == 1 (it consumes one unit)
    def flow_turbine_rule(mdl, j):
        return (sum(mdl.f[i, j] for i in nodes if i != j)
                - sum(mdl.f[j, k] for k in nodes if k != j)) == 1
    model.flow_turbine = pyo.Constraint(turbines, rule=flow_turbine_rule)

    # For the root: outflow == total turbines
    def flow_root_rule(mdl):
        return (sum(mdl.f[0, k] for k in nodes if k != 0)
                - sum(mdl.f[i, 0] for i in nodes if i != 0)) == num_turbines
    model.flow_root = pyo.Constraint(rule=flow_root_rule)

    # Flow upper bound linked to arc activation (big-M via total turbines)
    def flow_link_rule(mdl, i, j):
        return mdl.f[i, j] <= num_turbines * mdl.x[i, j]
    model.flow_link = pyo.Constraint(arcs, rule=flow_link_rule)

    # Capacity: each feeder string from root carries at most max_turbines_per_feeder
    def feeder_cap_rule(mdl, k):
        return mdl.f[0, k] <= max_turbines_per_feeder * mdl.x[0, k]
    model.feeder_cap = pyo.Constraint(turbines, rule=feeder_cap_rule)

    def obj_rule(mdl):
        return sum(cost(i, j) * mdl.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}