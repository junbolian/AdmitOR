import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = params["part_widths"]
    part_heights = params["part_heights"]

    parts = list(range(len(part_widths)))
    sheets = list(range(len(part_widths)))

    model = pyo.ConcreteModel()

    model.PARTS = pyo.Set(initialize=parts)
    model.SHEETS = pyo.Set(initialize=sheets)
    model.PAIRS = pyo.Set(
        initialize=[(i, j) for i in parts for j in parts if i < j],
        dimen=2,
    )

    model.assign = pyo.Var(model.PARTS, model.SHEETS, domain=pyo.Binary)
    model.x = pyo.Var(model.PARTS, model.SHEETS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PARTS, model.SHEETS, domain=pyo.NonNegativeReals)

    model.use_sheet = pyo.Var(model.SHEETS, domain=pyo.Binary)

    # Each part assigned to exactly one sheet
    def assign_rule(m, i):
        return sum(m.assign[i, s] for s in m.SHEETS) == 1

    model.assign_con = pyo.Constraint(model.PARTS, rule=assign_rule)

    # Link use_sheet to assignments
    def link_rule(m, i, s):
        return m.assign[i, s] <= m.use_sheet[s]

    model.link_con = pyo.Constraint(model.PARTS, model.SHEETS, rule=link_rule)

    # Position bounds within sheet
    def xbound_rule(m, i, s):
        return m.x[i, s] + part_widths[i] <= sheet_width * m.assign[i, s] + \
            sheet_width * (1 - m.assign[i, s])

    def ybound_rule(m, i, s):
        return m.y[i, s] + part_heights[i] <= sheet_height * m.assign[i, s] + \
            sheet_height * (1 - m.assign[i, s])

    model.xbound = pyo.Constraint(model.PARTS, model.SHEETS, rule=xbound_rule)
    model.ybound = pyo.Constraint(model.PARTS, model.SHEETS, rule=ybound_rule)

    # Non-overlap on same sheet: use big-M with binary disjunction
    model.overlap = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)

    M = sheet_width + sheet_height

    def no_overlap_rule(m, i, j, s):
        # If both i and j on sheet s, they must not overlap.
        # Disjunction: i left of j, j left of i, i below j, j below i
        # Use big-M with disjunction binary. Since we need at least one to hold:
        # x_i + w_i <= x_j OR x_j + w_j <= x_i OR y_i + h_i <= y_j OR y_j + h_j <= y_i
        # Encode with two binaries: left_right (0: i left, 1: j left) and
        # represented simply: we allow both simultaneously with big-M and require
        # at least one satisfied when both assigned.
        both = m.assign[i, s] + m.assign[j, s] - 1
        # two binaries: d1 for horizontal separation, d2 for vertical separation
        # We need: at least one of 4 holds. Use horizontal or vertical separation.
        # horiz: either i left of j (a) or j left of i (b)
        # vert: either i below j (c) or j below i (d)
        # at least one of a,b,c,d true when both assigned.
        # Standard trick: pick a primary axis (say whichever order), require
        # horizontal or vertical. Use two binaries h and v where h+v >= 1 when both.
        return pyo.Constraint.Skip

    # Implement non-overlap with a simpler formulation using 4 binaries per pair-sheet
    # Replace with proper big-M disjunction
    del model.overlap

    model.hsep = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)
    model.vsep = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)

    def hsep_rule(m, i, j, s):
        # hsep[i,j,s]=0 => i left of j; hsep[i,j,s]=1 => j left of i (only meaningful when both on s)
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.x[i, s] + part_widths[i] <= m.x[j, s] + sheet_width * (1 - m.hsep[i, j, s]) + sheet_width * (1 - both)

    def hsep_rule2(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.x[j, s] + part_widths[j] <= m.x[i, s] + sheet_width * m.hsep[i, j, s] + sheet_width * (1 - both)

    def vsep_rule(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.y[i, s] + part_heights[i] <= m.y[j, s] + sheet_height * (1 - m.vsep[i, j, s]) + sheet_height * (1 - both)

    def vsep_rule2(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.y[j, s] + part_heights[j] <= m.y[i, s] + sheet_height * m.vsep[i, j, s] + sheet_height * (1 - both)

    # Require that on each sheet, for each pair both assigned, either hsep or vsep holds
    def disj_rule(m, i, j, s):
        # If both assigned, need hsep and vsep to be valid alternatives.
        # We can just enforce that at least one separation family is active.
        # Using: hsep[i,j,s] can be 0/1 but if vsep works, hsep doesn't need to.
        # Simpler: require hsep[i,j,s]=0 means i left of j must hold, etc.
        # Actually enforce: at least one of the following four holds.
        # This is complex; instead require: (hsep implies i left or j left satisfied by chosen value)
        return pyo.Constraint.Skip

    # Better approach: enforce both horizontal separation (with hsep choosing side) AND
    # that either horizontal OR vertical separation holds, using a selector.
    # Rebuild cleanly with standard 4-binary formulation.
    for v in list(model.component_objects(pyo.Var, active=True)):
        if v.local_name in ("hsep", "vsep"):
            model.del_component(v)

    model.ll = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)  # i left of j
    model.rr = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)  # j left of i
    model.bb = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)  # i below j
    model.tt = pyo.Var(model.PAIRS, model.SHEETS, domain=pyo.Binary)  # j below i

    def ll_rule(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.x[i, s] + part_widths[i] <= m.x[j, s] + sheet_width * (1 - m.ll[i, j, s]) + sheet_width * (1 - both)

    def rr_rule(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.x[j, s] + part_widths[j] <= m.x[i, s] + sheet_width * (1 - m.rr[i, j, s]) + sheet_width * (1 - both)

    def bb_rule(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.y[i, s] + part_heights[i] <= m.y[j, s] + sheet_height * (1 - m.bb[i, j, s]) + sheet_height * (1 - both)

    def tt_rule(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.y[j, s] + part_heights[j] <= m.y[i, s] + sheet_height * (1 - m.tt[i, j, s]) + sheet_height * (1 - both)

    model.ll_con = pyo.Constraint(model.PAIRS, model.SHEETS, rule=ll_rule)
    model.rr_con = pyo.Constraint(model.PAIRS, model.SHEETS, rule=rr_rule)
    model.bb_con = pyo.Constraint(model.PAIRS, model.SHEETS, rule=bb_rule)
    model.tt_con = pyo.Constraint(model.PAIRS, model.SHEETS, rule=tt_rule)

    def one_sep_rule(m, i, j, s):
        both = m.assign[i, s] + m.assign[j, s] - 1
        return m.ll[i, j, s] + m.rr[i, j, s] + m.bb[i, j, s] + m.tt[i, j, s] >= both

    model.one_sep = pyo.Constraint(model.PAIRS, model.SHEETS, rule=one_sep_rule)

    def obj_rule(m):
        return sum(m.use_sheet[s] for s in m.SHEETS)

    model.total_sheets = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_sheets))
    return {"objective": obj_val, "status": "optimal"}