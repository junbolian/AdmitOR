import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    branch_capacity = params["branch_capacity"]
    num_dz = params["num_drop_zones"]
    n_total = params["num_nodes_total"]

    base = 0
    nodes = list(range(n_total))
    dz_nodes = list(range(1, n_total))

    # Directed candidate edges: i -> j with i != j.
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=nodes)
    model.D = pyo.Set(initialize=dz_nodes)
    model.A = pyo.Set(initialize=pairs, dimen=2)

    # x[i,j] = 1 if directed edge i->j selected (parent i of node j).
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # Each drop zone has exactly one incoming edge.
    def one_parent_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1
    model.one_parent = pyo.Constraint(model.D, rule=one_parent_rule)

    # Flow variables on each candidate edge.
    model.y = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    # Flow balance: each dz node consumes 1 unit.
    def flow_balance_rule(mdl, j):
        inflow = sum(mdl.y[i, j] for i in nodes if i != j)
        outflow = sum(mdl.y[j, k] for k in nodes if k != j)
        return inflow - outflow == 1
    model.flow_balance = pyo.Constraint(model.D, rule=flow_balance_rule)

    # Root supplies num_dz units.
    def root_supply_rule(mdl):
        outflow = sum(mdl.y[base, k] for k in nodes if k != base)
        inflow = sum(mdl.y[k, base] for k in nodes if k != base)
        return outflow - inflow == num_dz
    model.root_supply = pyo.Constraint(rule=root_supply_rule)

    # Base cannot be a child of anyone.
    def no_into_base_rule(mdl, i):
        return mdl.x[i, base] == 0
    model.no_into_base = pyo.Constraint(nodes, rule=no_into_base_rule)

    # Base cannot be a parent of itself (already excluded from A).
    # Link flow and selection.
    def link_rule(mdl, i, j):
        return mdl.y[i, j] <= num_dz * mdl.x[i, j]
    model.link = pyo.Constraint(model.A, rule=link_rule)

    # Branch capacity: flow from base to each direct child c <= branch_capacity.
    def branch_cap_rule(mdl, c):
        return mdl.y[base, c] <= branch_capacity
    model.branch_cap = pyo.Constraint(model.D, rule=branch_cap_rule)

    # Objective: sum of costs on selected edges.
    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j] for (i, j) in pairs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}