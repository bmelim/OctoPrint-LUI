from __future__ import division

__author__ = "Erik Heidstra <ErikHeidstra@live.nl>"

"""

Bolt scripts generator

Creates wiping and extruder calibration scripts for the Bolt and BoltPro

"""

import math

f_p = 1800      # Print speed (mm/min)
f_m = 12000     # Move speed  (mm/min)
f_w = 12000     # Wipe speed  (mm/min)
f_r = 3000      # Retraction speed (mm/min)
f_z = 1800      # Z-axis-speed (mm/min)
e_r = 2         # Retraction length (mm)
e_p = 2.1       # Prime length (mm)
z = 0.15        # Layer height
o = 1.1         # Overextrusion factor

#d_n = 0.35     # Nozzle diameter (irrelevant as we work with extrusion width)
d_f = 1.75      # Filament diameter
w_p = 0.39      # Extrusion width

n_layers = 1    # Number of layers to print. One is fine.

gCodeStart = [ 'G28', \
            'T0', \
            'M109 T0', \
            'M109 T1', \
            'M190', \
            'M107', \
            'G28', \
            'G90'
            ]

gCodeEnd =  [ 'G1 Z20 F600', \
            'G28 X0 Y0', \
            'M84', \
            'M107', \
            'M400' 
            # Don't turn of the heaters. Let LUI do that for us.
            ]

def linspace(start, stop, n):
    if n == 1:
        yield stop
        return
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i

def smallcircle(nPi, steps, r, xoffset, yoffset, eoffset):
    """
    Draws a small circle in gcode
    """    

    # Length of a segment of the circle
    l_p = r * nPi * math.pi / steps

    # Amount to extrude per segment
    e_n = l_p * o * A_p/A_f

    gcode = []
    i = 0

    e = eoffset
    
    for t in linspace(0, nPi*math.pi, steps):
        x = math.cos(t) * r + xoffset;
        y = math.sin(t) * r + yoffset;
        
        if i == 0:
            # Move to position
            gcode.append('G1 X{0:0.3f} Y{1:0.3f} E{2:0.3f} F{3:0.3f}'.format(x, y, e, f_m))
        elif i == 1:
            # Prime and begin circle
            e += e_p
            gcode.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r))
            e += e_n
            gcode.append('G1 X{0:0.3f} Y{1:0.3f} E{2:0.3f} F{3:0.3f}'.format(x, y, e, f_p))
        else:
            # Continue circle
            e += e_n
            gcode.append('G1 X{0:0.3f} Y{1:0.3f} E{2:0.3f} F{3:0.3f}'.format(x, y, e, f_p))
        
        i += 1
        
    return gcode, e

# Begin creating the scripts
for machine in ['bolt', 'boltpro']:
    
    bed_width = 367 # Helper to calculate center position of the bed

    if machine == "boltpro":
        bed_width = 376

    wiping_dist_x = 20 # Distance between bed edge and wipers (in x)
    wiping_pos_y = -33 # Y wiping position

    x_min = -37                 # Helper to calculate center position of the bed
    x_max = bed_width + x_min   # Helper to calculate the wiper position
    
    wipe = [[], []]

    wipe_t0_x1 = x_max - wiping_dist_x
    wipe_t0_x2 = x_max - 2
    wipe_t0_filename = "scripts/" + machine + "/snippets/" + machine + "_wipe_right.jinja2"

    wipe_t1_x1 = x_min + wiping_dist_x
    wipe_t1_x2 = x_min + 2
    wipe_t1_filename = "scripts/" + machine + "/snippets/" + machine + "_wipe_left.jinja2"
        
    # Right wiping sequence
    wipe[0] = [ 'G92 E0; zero extruder', 
                'G1 Y{0:.2f} F{1}; move to front of machine'.format(wiping_pos_y, f_m), 
                'G1 E15 F6000; extrude 15 mm fast', 
                'G1 E30 F150 ; extrude another 15 mm slow', 
                'G1 E28 F6000 ; retract 2mm', 
                'G4 S2; wait for 2 seconds', 
                '; perform wipe sequence', 
                'G1 X{0:.3f} F{1}'.format(wipe_t0_x1, f_w), 
                'G1 X{0:.3f} F{1}'.format(wipe_t0_x2, f_w), 
                'G1 X{0:.3f} F{1}'.format(wipe_t0_x1, f_w), 
                'G1 X{0:.3f} F{1}'.format(wipe_t0_x2, f_w), 
                'G92 E0; zero extruder']

    # Left wiping sequence
    wipe[1] = [ 'G92 E0; zero extruder', 
                'G1 Y{0:.2f} F{1}; move to front of machine'.format(wiping_pos_y, f_m), 
                'G1 E15 F6000; extrude 15 mm fast', 
                'G1 E30 F150 ; extrude another 15 mm slow', 
                'G1 E28 F6000 ; retract 2mm', 
                'G4 S2; wait for 2 seconds', 
                '; perform wipe sequence', 
                'G1 X{0:.3f} F{1}'.format(wipe_t1_x1, f_w), 
                'G1 X{0:.3f} F{1}'.format(wipe_t1_x2, f_w), 
                'G1 X{0:.3f} F{1}'.format(wipe_t1_x1, f_w), 
                'G1 X{0:.3f} F{1}'.format(wipe_t1_x2, f_w), 
                'G92 E0; zero extruder']

    # While we're at it, update the wiping sequences
    
    with open(wipe_t0_filename ,'w') as file:
        for line in wipe[0]:
            file.write(line + '\n')
    with open(wipe_t1_filename ,'w') as file:
        for line in wipe[1]:
            file.write(line + '\n')

    for pattern in ['1mm', '100um']:

        filename = 'scripts/{machine}/{machine}_bedwidthcalibration_{pattern}.gcode'.format(machine=machine,pattern=pattern)

        if pattern == '100um':
            n_lines_x = 11    # The number of lines to draw. Must be uneven (so 0 can be in the center)!
            n_lines_y = 17   # Whether or not to draw the horizontal y-axis lines
            offset = 0.1    # Difference between each line in mm (the accuracy of the calibration)
            xdiff = 10      # Distance between vertical lines in mm
            ydiff = 10      # Distance between horizontal lines in mm
            xymin = 190     # The y position of the bottom of the vertical lines
            yymin = 10      # The y position of the last (bottom) horizontal line
        elif pattern == '1mm':
            n_lines_x = 17    # The number of lines to draw. Must be uneven (so 0 can be in the center)!
            n_lines_y = 0   # Whether or not to draw the horizontal y-axis lines
            offset = 1      # Difference between each line in mm (the accuracy of the calibration)
            xdiff = 15      # Distance between vertical lines in mm
            ydiff = 15      # Distance between horizontal lines in mm
            xymin = 260     # The y position of the bottom of the vertical lines 
            yymin = 50      # (not used here) The y position of the last (bottom) horizontal line

        # X-Axis calibration settings: Vertical lines
        xheight = 50                            # The height of the vertical lines
        xwidth = xdiff*(n_lines_x-1)              # The total width of the vertical lines
        xxmin = x_min + (bed_width-xwidth) / 2  # The x position of the first (left) line (calculated as such that the 0 line is at the center of the bed)
        xymax = xymin+xheight                   # The y position of the top of the vertical lines

        # Y-Axis calibration settings: Horizontal lines
        yheight = ydiff*(n_lines_y-1)             # The total height of the horizontal lines
        ywidth = 50                             # The width of the horizontal (y-axis calibration) lines
        yxmin = x_min + (bed_width-ywidth) / 2  # The x position of the horizontal lines (calculated as such that the center of the line is at the center of the bed)
        yxmax = yxmin + ywidth                  # The x position of the right edge of the horizontal lines
        yymax = yymin + yheight                 # The y position of the first (top) horizontal line

        A_f = math.pi * math.pow(d_f/2, 2)                          # Filament cross sectional area
        A_p = w_p * z + (0.25 * math.pi -1) * math.pow(z,2)         # Printed path cross sectional area
        
        e_xp = o * A_p/A_f * xheight        # Extrusion length vertical lines (mm)
        e_yp = o * A_p/A_f * ywidth         # Extrusion length horizontal lines (mm)

        gCodeLines = []

        for i in range(n_layers):
            for T in [0, 1]:
                lz = i*2 * z + (T+1) * z
                gCodeLines.append(';Begin Tool {0:d}'.format(T))
                gCodeLines.append('T{0:d}'.format(T))

                # Z-hopping
                gCodeLines.append('G1 Z{0:0.3f} F{1:0.3f}'.format(lz+z, f_z))
        
                # Wipe
                gCodeLines.extend(wipe[T])
                # Wiping resets e to 0
                e = 0
                # X-axis
                for j in range(n_lines_x):
                    x1 = j * xdiff + xxmin
            
                    if T == 0 and j == (n_lines_x-1)/2:
                        # Draw a small circle when we're in the middle
                        gCodeLines.append(';Begin circle')
                
                        # Draw circle (2pi, 50 steps, 4 mm radius, at 10mm y-offset)
                        circle, e = smallcircle(2, 50, 4, x1, xymin - 10, e)
                        gCodeLines.extend(circle)

                         # Retract
                        e -= e_r
                        gCodeLines.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r)) 
                    elif T == 1:
                        # For tool1, start with an offset, which gets smaller towards the middle line
                        x1 = x1 + (j-((n_lines_x-1)/2))*offset
            
                    y1 = xymin 

                    x2 = x1
                    y2 = xymax

                    gCodeLines.append(';Vertical line #{0:d} Tool {1:d}'.format(j, T))

                    # Move to position
                    gCodeLines.append('G1 X{0:0.3f} Y{1:0.3f} F{2:0.3f}'.format(x1, y1, f_m))

                    # Hop
                    if j == 0:
                        gCodeLines.append('G1 Z{0:0.3f} F{1:0.3f}'.format(lz, f_z))

                    # Prime
                    e += e_p
                    gCodeLines.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r))

                    # Draw line
                    e += e_xp
                    gCodeLines.append('G1 X{0:0.3f} Y{1:0.3f} E{2:0.3f} F{3:0.3f}'.format(x2, y2, e, f_p))

                    # Retract
                    e -= e_r
                    gCodeLines.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r)) 

                # Z-hopping
                gCodeLines.append('G1 Z{0:0.3f} F{1:0.3f}'.format(lz+z, f_z))

                # Y-axis
                for j in range(n_lines_y):
                    y1 = yymax - j * ydiff

                    if T == 0 and j == (n_lines_y-1)/2 :
                        # Draw a small circle when we're in the middle
                        gCodeLines.append(';Begin circle')
                    
                        # Draw circle (2pi, 50 steps, 4 mm radius, at 10mm x-offset)
                        circle, e = smallcircle(2, 50, 4, yxmin - 10, y1, e)
                        gCodeLines.extend(circle)
                    
                        # Retract
                        e -= e_r
                        gCodeLines.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r)) 
                    elif T == 1:
                        # For tool1, start with an offset, which gets smaller towards the middle line
                        y1 = y1 - (j-((n_lines_y-1)/2))*offset

                    x1 = yxmin
                    y2 = y1
                    x2 = yxmax

                    gCodeLines.append(';Horizontal line #{0:d} Tool {1:d}'.format(j, T))
       
                    # Move to position   
                    gCodeLines.append('G1 X{0:0.3f} Y{1:0.3f} F{2:0.3f}'.format(x1, y1, f_m))
                
                    # Hop
                    if j == 0:
                        gCodeLines.append('G1 Z{0:0.3f} F{1:0.3f}'.format(lz, f_z))
                    
                    # Prime
                    e += e_p    
                    gCodeLines.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r))
                   
                
                    # Print line
                    e += e_yp
                    gCodeLines.append('G1 X{0:0.3f} Y{1:0.3f} E{2:0.3f} F{3:0.3f}'.format(x2, y2, e, f_p))
                
                    # Retract
                    e -= e_r
                    gCodeLines.append('G1 E{0:0.3f} F{1:0.3f}'.format(e, f_r)) 

            

        with open(filename,'w') as file:
            for line in gCodeStart:
                file.write(line + '\n')
            for line in gCodeLines:
                file.write(line + '\n')
            for line in gCodeEnd:
                file.write(line + '\n')
