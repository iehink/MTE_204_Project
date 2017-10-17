import tkinter as tk
import threading
import time
import copy
import vector

#CONSTANTS
INSTRUCTION_MARGIN = 50
INSTRUCTION_TEXT = """Instructions:
- Click on the white space to the right to place a planet.
- A popup will apppear, input the requested information 
(position, velocity, and mass).
- Right click on a planet to delete it.
- Click the clear button to delete everthing.
- Click run to run the simulation.
Have fun! :)"""

R = 3 #radius of drawn planets
G = 6.67408 * pow(10,-11) #gravitational constant, m^3 kg^-1 s^-2 
TIME = 604800 #time interval for calculating next position, 604800 seconds = 1 week

class PlanetObject(object):
    def __init__(self, mass, pos, vel, tag):
        self.mass = mass
        self.pos = pos
        self.nextpos = pos
        self.vel = vel
        self.nextvel = vel
        self.tag = tag
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
        self.planet_list = list()
        self.old_planet_list = None
        self.root = parent
        self.motion_thread = None

        # Text layout
        self.instruction_title = tk.Label(parent, text=INSTRUCTION_TEXT)
        self.instruction_title.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # Button layout
        self.create_button = tk.Button(parent, text="Create", command=self.create_planet)
        self.create_button.grid(row=7, column=0, columnspan=2)
        self.clear_button = tk.Button(parent, text="Clear", command=self.clear_canvas)
        self.clear_button.grid(row=1, column=0, sticky=tk.N)
        self.reset_button = tk.Button(parent, text="Reset", command=self.reset_canvas)
        self.reset_button.grid(row=1, column=1, sticky=tk.N)
        self.exit_button = tk.Button(parent, text="Exit", command=self.exit)
        self.exit_button.grid(row=8, column=0)
        self.run_button = tk.Button(parent, text="Run", command=self.run)
        self.run_button.grid(row=8, column=1)

        # Canvas layout
        self.canvas = tk.Canvas(parent, bg="white", 
                                width=(parent.winfo_screenwidth() - self.instruction_title.winfo_reqwidth()),
                                height=parent.winfo_screenheight())
        self.canvas.grid(row=0, column=2, rowspan=10, sticky=tk.E)
        self.canvas_height = self.canvas.winfo_reqheight()
        self.canvas_width = self.canvas.winfo_reqwidth()
        self.canvas.create_line(0, self.canvas_height / 2, self.canvas_width, self.canvas_height / 2, fill="#000000")
        self.canvas.create_line(self.canvas_width / 2, 0, self.canvas_width / 2, self.canvas_height, fill="#000000")

        # Input form layout
        self.mass_label = tk.Label(parent, text="mass [kg*10^20]: ")
        self.mass_label.grid(row=2, column=0)
        self.mass_entry = tk.Entry(parent)
        self.mass_entry.grid(row=2, column=1)
        self.posx_label = tk.Label(parent, text="x position [km*10^6]: ")
        self.posx_label.grid(row=3, column=0)
        self.posx_entry = tk.Entry(parent)
        self.posx_entry.grid(row=3, column=1)
        self.posy_label = tk.Label(parent, text="y position [km*10^6]: ")
        self.posy_label.grid(row=4, column=0)
        self.posy_entry = tk.Entry(parent)
        self.posy_entry.grid(row=4, column=1)
        self.velx_label = tk.Label(parent, text="x velocity [m/s]: ")
        self.velx_label.grid(row=5, column=0)
        self.velx_entry = tk.Entry(parent)
        self.velx_entry.grid(row=5, column=1)
        self.vely_label = tk.Label(parent, text="y velocity [m/s]: ")
        self.vely_label.grid(row=6, column=0)
        self.vely_entry = tk.Entry(parent)
        self.vely_entry.grid(row=6, column=1)

        #Test output boxes
##        self.out1 = tk.Label(parent, text=" ")
##        self.out1.grid(row=0, column=0)
##        self.out2 = tk.Label(parent, text=G)
##        self.out2.grid(row=0, column=1)

    def create_planet(self):
        # Save the entry form data
        pos = [float(self.posx_entry.get()), float(self.posy_entry.get())] #in units of m*10^9
        mass = float(self.mass_entry.get()) #in units of kg*10^20
        vel = [float(self.velx_entry.get()), float(self.vely_entry.get())] #in units of m/s

        mass = mass*pow(10,20)
        pos = vector.scalarMult(pos, pow(10, 9))

        # Draw and save the point
        self.draw_planet(mass, pos, vel)

        # Clear the Entry Form
        self.mass_entry.delete(0, tk.END)
        self.posx_entry.delete(0, tk.END)
        self.posy_entry.delete(0, tk.END)
        self.velx_entry.delete(0, tk.END)
        self.vely_entry.delete(0, tk.END)

    def draw_planet(self, mass, pos, vel):
        x1, y1 = (int(pos[0]*pow(10, -9)) - R + self.canvas_width / 2), (int(pos[1]*pow(10, -9)) - R + self.canvas_height / 2)
        x2, y2 = (int(pos[0]*pow(10, -9)) + R + self.canvas_width / 2), (int(pos[1]*pow(10, -9)) + R + self.canvas_height / 2)
        tag = self.canvas.create_oval(int(x1), int(y1), int(x2), int(y2), fill="#0000ff")
        new_planet = PlanetObject(mass, pos, vel, tag)
        self.planet_list.append(new_planet)

    def delete_planet(self, event):
        can = event.widget
        if (isinstance(can, tk.Canvas)):
            x = can.canvasx(event.x)
            y = can.canvasy(event.y)
            for planet_index in range(len(self.planet_list)):
                planet = self.planet_list[planet_index]
                if (planet.pos[0] <= R + x and planet.pos[0] >= x - R):
                    if (planet.pos[1] <= R + y and planet.pos[1] >= y-R):
                        # Delete the planet
                        self.canvas.delete(planet.tag)
                        del(self.planet_list[planet_index])

    def clear_canvas(self):
        self.canvas.delete(tk.ALL)
        self.canvas.create_line(0, self.canvas_height / 2, self.canvas_width, self.canvas_height / 2, fill="#000000")
        self.canvas.create_line(self.canvas_width / 2, 0, self.canvas_width / 2, self.canvas_height, fill="#000000")

    def reset_canvas(self):
        if (self.old_planet_list is None):
            return
        self.clear_canvas()
        # Reset the planet list to what it was before the simulation was run
        # and redraw the canvas
        self.planet_list = []
        for planet in self.old_planet_list:
            self.draw_planet(planet.mass, planet.pos, planet.vel)

    def run(self):
        self.old_planet_list = copy.deepcopy(self.planet_list)
        self.run_button["text"] = "Stop"
        self.run_button["command"] = self.stop_running
        self.motion_thread = threading.Thread(target=self.motion)
        self.motion_thread.start() 

    def stop_running(self):
        if(self.motion_thread is not None):
            self.exit_flag = True
            self.motion_thread.join()
        self.run_button["text"] = "Run"
        self.run_button["command"] = self.run

    def motion(self):
        self.exit_flag = False
        while(not self.exit_flag):
            self.move_planets()
        exit_flag = False

    def exit(self):
        if(self.motion_thread is not None):
            self.stop_running()
            self.motion_thread.join()
        self.root.destroy()

    def move_planets(self):
        converted_planet_list = self.next_pos()
        for planet in converted_planet_list:
            print(planet[0])
            print(planet[1])
            # planet[2] is the oval's tag in the canvas
            # planet[0] is the planet's converted x position
            # planet[1] is the planet's converted y position
            self.canvas.coords(planet[2],
                               planet[0] - R + self.canvas_width / 2,
                               planet[1] - R + self.canvas_height / 2,
                               planet[0] + R + self.canvas_width / 2,
                               planet[1] + R + self.canvas_height / 2)
        time.sleep(1)

    #runge kutta: pos(i+1) = pos(i) + vel(i)*TIME + 1/6 * (k1+2k2+2k3+k4)*TIME^2
    #k1 = f(y)
    #k2 = f(y + 1/2k1h)
    #k3 = f(y + 1/2k2h)
    #k4 = f(y+k3h)

    #Finds the next position of each planet using the Runge Kutta Method
    #NOTE:
    #   Finding the k value and finding the next velocity/position need to be in different loops
    #   This prevents the changing of one position from effecting the other k predictions
    def next_pos(self):
        #Find k1 for each planet
        for planet in self.planet_list:
            planet.k1 = self.slope(planet.nextvel, planet)
##            self.out1["text"] = planet.pos[0]
##            self.out2["text"] = planet.pos[1]

        #Use k1 to find predicted next velocity and position
        for planet in self.planet_list:
            planet.nextvel = vector.add(planet.vel, vector.scalarMult(planet.k1, 1/2*TIME))
            planet.v1 = planet.nextvel
            planet.nextpos = vector.add(planet.pos, vector.scalarMult(planet.nextvel, 1/2*TIME))

        #Find k2 for each planet
        for planet in self.planet_list:        
            planet.k2 = self.slope(planet.nextvel, planet)

        #Use k2 to find predicted next velocity and position
        for planet in self.planet_list:
            planet.nextvel = vector.add(planet.vel, vector.scalarMult(planet.k2, 1/2*TIME))
            planet.v2 = planet.nextvel
            planet.nextpos = vector.add(planet.pos, vector.scalarMult(planet.nextvel, 1/2*TIME))

        #Find k3 for each planet
        for planet in self.planet_list:
            planet.k3 = self.slope(planet.nextvel, planet)

        #Use k3 to find predicted next velocity and position
        for planet in self.planet_list:
            planet.nextvel = vector.add(planet.vel, vector.scalarMult(planet.k3, TIME))
            planet.v3 = planet.nextvel
            planet.nextpos = vector.add(planet.pos, vector.scalarMult(planet.nextvel, TIME))

        #Find k4 for each planet
        for planet in self.planet_list:
            planet.k4 = self.slope(planet.nextvel, planet)
            planet.v4 = vector.add(planet.vel, vector.scalarMult(planet.k4, TIME))

        #Use k values to find velocity and position
        for planet in self.planet_list:
            planet.vel = vector.add(planet.vel, vector.scalarMult(vector.add(vector.add(vector.add(planet.k1, vector.scalarMult(planet.k2, 2)), vector.scalarMult(planet.k3, 2)), planet.k4), TIME/6))
            planet.pos = vector.add(vector.add(planet.pos, vector.scalarMult(planet.vel, TIME)), vector.scalarMult(vector.add(vector.add(vector.add(planet.v1, vector.scalarMult(planet.v2, 2)), vector.scalarMult(planet.v3, 2)), planet.v4), TIME/6))
            #planet.pos = vector.add(planet.pos, vector.scalarMult(planet.vel, TIME))
            planet.nextvel = planet.vel
            planet.nextpos = planet.pos

        converted_planet_list = []
        for planet in self.planet_list:
            # convert units here, then return another list
            temp_data = []
            temp_data.append(int(planet.pos[0]*pow(10,-9)))
            temp_data.append(int(planet.pos[1]*pow(10,-9)))
            temp_data.append(planet.tag)
            converted_planet_list.append(temp_data)
            
        return converted_planet_list

    #Uses the predicted next velocity and next position values to find the slope of the function
    def slope(self, r, ref_planet):
        total = [0,0]
        for planet in self.planet_list:
            if (ref_planet != planet):
                total = vector.add(total, vector.scalarMult(vector.sub(r, planet.nextpos),(planet.mass/pow(vector.mag(vector.sub(r, planet.nextpos)),3))))
        return(vector.scalarMult(total, G))

if __name__ == "__main__":
    root = tk.Tk()

    # Define main window qualities
    root.title("Solar System Sandbox")
    root.resizable(width=False, height=False)
    root.state("zoomed")

    master = RootContents(root)

    # Bindings
    root.bind("<Button-3>", master.delete_planet)

    # Execute mainloop
    root.mainloop()
