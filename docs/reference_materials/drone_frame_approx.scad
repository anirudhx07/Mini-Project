// Approximate recreation of the white 3D-printed quadcopter frame in the supplied photos.
// Units: millimetres. This is a visual approximation, not the original manufacturer's CAD.
// Edit the parameters below to fit your motors, screws, and electronics.

$fn = 64;

thickness = 3.0;
overall_span = 120;       // approximate tip-to-tip diagonal span
motor_ring_d = 15;
motor_hole_d = 6.0;       // verify against your motor screws before printing
arm_width = 8.0;
arm_slot_width = 2.2;
center_w = 48;
center_h = 54;
center_slot_w = 4.0;
center_slot_h = 38;
tab_w = 5.5;
tab_h = 4.0;
tab_offset_y = 12;

motor_pos = 42.5;         // motor-hole coordinate on each X axis
arm_root = 17.5;

module capsule2d(p1, p2, d) {
    hull() {
        translate(p1) circle(d=d);
        translate(p2) circle(d=d);
    }
}

module motor_arm(sx, sy) {
    // broad arm linking central frame to circular motor mount
    hull() {
        translate([sx*arm_root, sy*arm_root]) circle(d=arm_width);
        translate([sx*motor_pos, sy*motor_pos]) circle(d=motor_ring_d);
    }
}

module motor_slot(sx, sy) {
    // narrow relief slot running along each arm
    capsule2d([sx*23, sy*23], [sx*37, sy*37], arm_slot_width);
}

module central_openings() {
    // Two rounded polygonal windows, separated by the characteristic X-shaped web.
    polygon(points=[
        [-8, 23], [8, 23], [9.5, 20], [9.5, 13],
        [7.5, 9], [0, 5], [-7.5, 9], [-9.5, 13], [-9.5, 20]
    ]);
    polygon(points=[
        [-7.5, -9], [0, -5], [7.5, -9], [9.5, -13],
        [9.5, -20], [7.5, -23], [-7.5, -23], [-9.5, -20],
        [-9.5, -13]
    ]);
}

module frame_2d() {
    difference() {
        union() {
            // central rectangular backbone
            square([center_w, center_h], center=true);

            // Four diagonal arms and round motor pads
            for (sx=[-1,1], sy=[-1,1]) {
                motor_arm(sx, sy);
                translate([sx*motor_pos, sy*motor_pos]) circle(d=motor_ring_d);
            }

            // Small lateral mounting tabs, two on each side
            for (sx=[-1,1], yy=[-tab_offset_y, tab_offset_y]) {
                translate([sx*(center_w/2+tab_w/2-0.3), yy])
                    square([tab_w, tab_h], center=true);
            }
        }

        // Four motor screw holes
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*motor_pos, sy*motor_pos]) circle(d=motor_hole_d);

        // Long slots inside diagonal arms
        for (sx=[-1,1], sy=[-1,1]) motor_slot(sx, sy);

        // Two long vertical slots beside the center windows
        for (sx=[-1,1])
            translate([sx*12.3, 0])
                hull() {
                    translate([0,-center_slot_h/2+2]) circle(d=center_slot_w);
                    translate([0, center_slot_h/2-2]) circle(d=center_slot_w);
                }

        central_openings();
    }
}

linear_extrude(height=thickness)
    frame_2d();
