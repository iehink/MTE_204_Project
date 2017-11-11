import tkinter as tk
import threading
import time
import copy
import vector

#CONSTANTS
INSTRUCTION_MARGIN = 50
INSTRUCTION_TEXT = """INSTRUCTIONS:
-Fill in the required fields below
-Click 'Create' to add the planet to the sandbox
-Click 'Run' to start the simulation, 'Stop' to pause it
-'Reset' will return the planets to their initial states
-Click on a planet to display information about it
-Right-click to delete a planet
"""
DIVIDER = """__________________________________________________________________"""

R = 3 # radius of drawn planets
G = 6.67408 * pow(10,-11) # gravitational constant, m^3 kg^-1 s^-2 
TIME = 2700 # 2700 seconds = 1/32 day

# Defines a planet object
class PlanetObject(object):
    # Initializes new planet objects
    def __init__(self, name, mass, pos, vel, tag):
        self.tag = tag
        self.name = name
        self.mass = mass
        self.pos = pos
        self.vel = vel

        # Holds intermediate values for position and velocity during calculations
        self.nextpos = pos
        self.nextvel = vel

        # Holds the intermediate slopes calculated by the Runge-Kutta method
        self.k1 = 0
        self.k2 = 0
        self.k3 = 0
        self.k4 = 0
        self.v1 = 0
        self.v2 = 0
        self.v3 = 0
        self.v4 = 0

class RootContents(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.planet_list = list() # A list of planets created by the user
        self.old_planet_list = None # The original values of the planets for use in resetting
        self.root = parent
        self.motion_thread = None
        
        self.exit_flag = False # Signals when the simulation should stop
        self.first_run = True # Tracks whether this is the first time the simulation has been run since the last clear
        self.time_Passed = 0 # Tracks the time that the simulation has processed

        # Text layout
        self.instruction_title = tk.Label(parent, text=(INSTRUCTION_TEXT+DIVIDER), justify=tk.LEFT)
        self.instruction_title.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        self.time_label = tk.Label(parent, text="Time passed: 0 days", justify=tk.LEFT)
        self.time_label.grid(row=1, column=0, columnspan=2)

        # Button layout
        self.create_button = tk.Button(parent, text="Create", command=self.create_planet)
        self.create_button.grid(row=9, column=0, columnspan=2)
        self.clear_button = tk.Button(parent, text="Clear", command=self.clear_canvas)
        self.clear_button.grid(row=2, column=0, sticky=tk.N)
        self.reset_button = tk.Button(parent, text="Reset", command=self.reset_canvas)
        self.reset_button.grid(row=2, column=1, sticky=tk.N)
        self.exit_button = tk.Button(parent, text="Exit", command=self.exit)
        self.exit_button.grid(row=10, column=0)
        self.run_button = tk.Button(parent, text="Run", command=self.run)
        self.run_button.grid(row=10, column=1)

        # Canvas layout
        self.canvas = tk.Canvas(parent, bg="white", 
                                width=(parent.winfo_screenwidth() - self.instruction_title.winfo_reqwidth()),
                                height=parent.winfo_screenheight())
        self.canvas.grid(row=0, column=2, rowspan=12, sticky=tk.E)
        self.canvas_height = self.canvas.winfo_reqheight()
        self.canvas_width = self.canvas.winfo_reqwidth()
        self.canvas.create_line(0, self.canvas_height / 2, self.canvas_width, self.canvas_height / 2, fill="#000000")
        self.canvas.create_line(self.canvas_width / 2, 0, self.canvas_width / 2, self.canvas_height, fill="#000000")

        # Input form layout
        self.name_label = tk.Label(parent, text="Name: ")
        self.name_label.grid(row=3, column=0)
        self.name_entry = tk.Entry(parent)
        self.name_entry.grid(row=3, column=1)
        self.mass_label = tk.Label(parent, text="Mass [kg*10^20]: ")
        self.mass_label.grid(row=4, column=0)
        self.mass_entry = tk.Entry(parent)
        self.mass_entry.grid(row=4, column=1)
        self.posx_label = tk.Label(parent, text="x-Position [km*10^6]: ")
        self.posx_label.grid(row=5, column=0)
        self.posx_entry = tk.Entry(parent)
        self.posx_entry.grid(row=5, column=1)
        self.posy_label = tk.Label(parent, text="y-Position [km*10^6]: ")
        self.posy_label.grid(row=6, column=0)
        self.posy_entry = tk.Entry(parent)
        self.posy_entry.grid(row=6, column=1)
        self.velx_label = tk.Label(parent, text="x-Velocity [km/s]: ")
        self.velx_label.grid(row=7, column=0)
        self.velx_entry = tk.Entry(parent)
        self.velx_entry.grid(row=7, column=1)
        self.vely_label = tk.Label(parent, text="y-Velocity [km/s]: ")
        self.vely_label.grid(row=8, column=0)
        self.vely_entry = tk.Entry(parent)
        self.vely_entry.grid(row=8, column=1)

    # Receives data from the user and formats it
    def create_planet(self):
        # Saves the entry form data
        name = self.name_entry.get()
        pos = [float(self.posx_entry.get()), float(self.posy_entry.get())] # in units of m*10^9
        mass = float(self.mass_entry.get()) # in units of kg*10^20
        vel = [float(self.velx_entry.get()), float(self.vely_entry.get())] # in units of m/s*10^3

        # Modifies to match units used in calculations
        mass = mass*pow(10,20)
        pos = vector.scalarMult(pos, pow(10, 9))
        vel = vector.scalarMult(vel, pow(10, 3))

        # Draws and saves the point
        self.draw_planet(name, mass, pos, vel)

        # Clears the Entry Form
        self.name_entry.delete(0, tk.END)
        self.mass_entry.delete(0, tk.END)
        self.posx_entry.delete(0, tk.END)
        self.posy_entry.delete(0, tk.END)
        self.velx_entry.delete(0, tk.END)
        self.vely_entry.delete(0, tk.END)

    # Draws a planet on the canvas and creates a new planet object
    def draw_planet(self, name, mass, pos, vel):
        # Draws the planet
        x1, y1 = (int(pos[0]*pow(10, -9)) - R + self.canvas_width / 2), (-1*int(pos[1]*pow(10, -9)) - R + self.canvas_height / 2)
        x2, y2 = (int(pos[0]*pow(10, -9)) + R + self.canvas_width / 2), (-1*int(pos[1]*pow(10, -9)) + R + self.canvas_height / 2)
        tag = self.canvas.create_oval(int(x1), int(y1), int(x2), int(y2), fill="#0000ff")

        #Creates a new planet and adds it to the planet list
        new_planet = PlanetObject(name, mass, pos, vel, tag)
        self.planet_list.append(new_planet)

    # Removes the oval from the canvas and the planet from the planet list
    def delete_planet(self, event):
        can = event.widget
        if (isinstance(can, tk.Canvas)):
            if (can.type(tk.CURRENT) != "line"):
                for planet_index in range(len(self.planet_list)):
                    if (self.planet_list[planet_index].tag == tk.CURRENT):
                        del(self.planet_list[planet_index])
                self.canvas.delete(tk.CURRENT)

    # Removes all ovals from the canvas and empties the planet list
    def clear_canvas(self):
        self.canvas.delete(tk.ALL)
        self.canvas.create_line(0, self.canvas_height / 2, self.canvas_width, self.canvas_height / 2, fill="#000000")
        self.canvas.create_line(self.canvas_width / 2, 0, self.canvas_width / 2, self.canvas_height, fill="#000000")
        self.planet_list = []
        self.time_Passed = 0
        self.first_run = True

    # Resets the canvas and returns the planets to their original states
    def reset_canvas(self):
        if (self.old_planet_list is None):
            return
        self.clear_canvas()
        self.time_Passed = 0
        self.time_label.configure(text=("Time passed: " + str(int(self.time_Passed/86400))  + " days"))
        
        # Resets the planet list to what it was before the simulation was run
        # and redraws the canvas (this adds the planets back into the planet list)
        self.planet_list = []
        for planet in self.old_planet_list:
            self.draw_planet(planet.name, planet.mass, planet.pos, planet.vel)

    # Starts the simulation
    def run(self):
        # Makes a copy of the planets if this is the first time the simulation has been run (for use with reset_canvas)
        if (self.first_run == True):
            self.old_planet_list = copy.deepcopy(self.planet_list)
            self.first_run = False
        self.run_button["text"] = "Stop"
        self.run_button["command"] = self.stop_running
        self.motion_thread = threading.Thread(target=self.motion)
        self.motion_thread.start()

    # Stops the simulation from running
    def stop_running(self):
        self.exit_flag = True
        self.motion_thread = None
        self.run_button["text"] = "Run"
        self.run_button["command"] = self.run

    # Loops while calling move_planets and tracking the time passed
    def motion(self):
        self.exit_flag = False
        while(not self.exit_flag):
            self.move_planets()
            self.time_Passed = self.time_Passed + TIME
            self.time_label.configure(text=("Time passed: " + str(int(self.time_Passed/86400))  + " days")) # outputs the time passed in days

    # Shuts down the program
    def exit(self):
        self.stop_running()
        self.root.destroy()

    # Draws the new position of each planet
    def move_planets(self):
        converted_planet_list = self.next_pos()
        for planet in converted_planet_list:
            # planet[2] is the oval's tag in the canvas
            # planet[0] is the planet's converted x position
            # planet[1] is the planet's converted y position
            self.canvas.coords(planet[2],
                               planet[0] - R + self.canvas_width / 2,
                               -1*planet[1] - R + self.canvas_height / 2,
                               planet[0] + R + self.canvas_width / 2,
                               -1*planet[1] + R + self.canvas_height / 2)

    # Finds the next position of each planet using the Runge-Kutta Method
    # k1 through k4 track intermediate values of acceleration used by the Runge Kutta Method
    # v1 through v4 track intermediate values of velocity used by the Runge Kutta Method
    def next_pos(self):
        # Finds k1 for each planet
        for planet in self.planet_list:
            planet.k1 = self.slope(planet.nextpos, planet)

        # Uses k1 to find the predicted next velocity and position
        for planet in self.planet_list:
            planet.nextvel = vector.add(planet.vel, vector.scalarMult(planet.k1, 1/2*TIME))
            planet.v1 = planet.nextvel
            planet.nextpos = vector.add(planet.pos, vector.scalarMult(planet.nextvel, 1/2*TIME))

        # Finds k2 for each planet
        for planet in self.planet_list:        
            planet.k2 = self.slope(planet.nextpos, planet)

        # Uses k2 to find predicted next velocity and position
        for planet in self.planet_list:
            planet.nextvel = vector.add(planet.vel, vector.scalarMult(planet.k2, 1/2*TIME))
            planet.v2 = planet.nextvel
            planet.nextpos = vector.add(planet.pos, vector.scalarMult(planet.nextvel, 1/2*TIME))

        # Finds k3 for each planet
        for planet in self.planet_list:
            planet.k3 = self.slope(planet.nextpos, planet)

        # Uses k3 to find predicted next velocity and position
        for planet in self.planet_list:
            planet.nextvel = vector.add(planet.vel, vector.scalarMult(planet.k3, TIME))
            planet.v3 = planet.nextvel
            planet.nextpos = vector.add(planet.pos, vector.scalarMult(planet.nextvel, TIME))

        # Finds k4 for each planet
        for planet in self.planet_list:
            planet.k4 = self.slope(planet.nextpos, planet)
            planet.v4 = vector.add(planet.vel, vector.scalarMult(planet.k4, TIME))

        # Uses k values to find velocity and position
        for planet in self.planet_list:
            # Uses classical fourth order Runge Kutta to calculate the next velocity 
            planet.vel = vector.add(planet.vel, vector.scalarMult(vector.add(vector.add(vector.add(planet.k1, vector.scalarMult(planet.k2, 2)), vector.scalarMult(planet.k3, 2)), planet.k4), TIME/6))
            # Uses classical fourth order Runge Kutta to calculate the next position
            planet.pos = vector.add(planet.pos, vector.scalarMult(vector.add(vector.add(vector.add(planet.v1, vector.scalarMult(planet.v2, 2)), vector.scalarMult(planet.v3, 2)), planet.v4), TIME/6))

            planet.nextvel = planet.vel
            planet.nextpos = planet.pos

        # Creates a list that can be used to output to the canvas
        converted_planet_list = []
        for planet in self.planet_list:
            # Converts units here, then returns another list
            temp_data = []
            temp_data.append(int(planet.pos[0]*pow(10,-9)))
            temp_data.append(int(planet.pos[1]*pow(10,-9)))
            temp_data.append(planet.tag)
            converted_planet_list.append(temp_data)
            
        return converted_planet_list

    # Uses the predicted next position values to find the acceleration of the planet
    def slope(self, pos, ref_planet):
        total = [0,0] # Tracks the total acceleration on the planet
        for planet in self.planet_list:
            if (ref_planet != planet):
                # Uses Newton's Law of Universial Gravitation to find the component of acceleration caused by each other planet in the system
                total = vector.add(total, vector.scalarMult(vector.sub(planet.nextpos, pos),(planet.mass/pow(vector.mag(vector.sub(planet.nextpos, pos)),3))))
        return(vector.scalarMult(total, G))

    # Displays the info on a planet when it is clicked on
    def display_info(self, event):
        if self.canvas.find_withtag(tk.CURRENT):
            tag = self.canvas.find_withtag(tk.CURRENT)[0]
            for planet in self.planet_list:
                if (planet.tag == tag):
                    planet_data = """PLANET DATA:
Name: """ + str(planet.name) + """
Mass: """ + str(planet.mass/pow(10,20)) + """ [kg*10^20]
x-Position: """ + str(planet.pos[0]/pow(10,9)) + """ [km*10^6]
y-Position: """ + str(planet.pos[1]/pow(10,9)) + """ [km*10^6]
x-Velocity: """ + str(planet.vel[0]/pow(10,3)) + """ [km/s]
y-Velocity: """ + str(planet.vel[1]/pow(10,3)) + """ [km/s]
"""
                    self.instruction_title.configure(text=(planet_data+DIVIDER))
        else:
            self.instruction_title.configure(text=(INSTRUCTION_TEXT+DIVIDER))


if __name__ == "__main__":
    root = tk.Tk()

    # Defines main window qualities
    root.title("Solar System Sandbox")
    root.resizable(width=False, height=False)
    root.state("zoomed")

    master = RootContents(root)

    # Bindings
    master.canvas.bind("<Button-1>", master.display_info)
    root.bind("<Button-3>", master.delete_planet)

    # Execute mainloop
    root.mainloop()
