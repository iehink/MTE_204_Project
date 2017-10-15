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
TIME = 1 #time interval for calculating next position, seconds

class PlanetObject(object):
    def __init__(self, mass, pos, vel, tag):
        self.mass = mass
        self.pos = pos
        self.vel = vel
        self.tag = tag

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
        self.mass_label = tk.Label(parent, text="mass: ")
        self.mass_label.grid(row=2, column=0)
        self.mass_entry = tk.Entry(parent)
        self.mass_entry.grid(row=2, column=1)
        self.posx_label = tk.Label(parent, text="x position: ")
        self.posx_label.grid(row=3, column=0)
        self.posx_entry = tk.Entry(parent)
        self.posx_entry.grid(row=3, column=1)
        self.posy_label = tk.Label(parent, text="y position: ")
        self.posy_label.grid(row=4, column=0)
        self.posy_entry = tk.Entry(parent)
        self.posy_entry.grid(row=4, column=1)
        self.velx_label = tk.Label(parent, text="x velocity: ")
        self.velx_label.grid(row=5, column=0)
        self.velx_entry = tk.Entry(parent)
        self.velx_entry.grid(row=5, column=1)
        self.vely_label = tk.Label(parent, text="y velocity: ")
        self.vely_label.grid(row=6, column=0)
        self.vely_entry = tk.Entry(parent)
        self.vely_entry.grid(row=6, column=1)

    def create_planet(self):
        # Save the entry form data
        pos = [int(self.posx_entry.get()), int(self.posy_entry.get())]
        mass = int(self.mass_entry.get())
        vel = [int(self.velx_entry.get()), int(self.vely_entry.get())]

        # Draw and save the point
        self.draw_planet(mass, pos, vel)

        # Clear the Entry Form
        self.mass_entry.delete(0, tk.END)
        self.posx_entry.delete(0, tk.END)
        self.posy_entry.delete(0, tk.END)
        self.velx_entry.delete(0, tk.END)
        self.vely_entry.delete(0, tk.END)

    def draw_planet(self, mass, pos, vel):
        x1, y1 = (pos[0] - R), (pos[1] - R)
        x2, y2 = (pos[0] + R), (pos[1] + R)
        tag = self.canvas.create_oval(x1, y1, x2, y2, fill="#0000ff")
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
        self.exit_flag = True
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
        for planet in self.planet_list:
            (new_posx, new_posy) = self.do_the_math(planet)
            self.canvas.coords(planet.tag, new_posx - R, new_posy - R, new_posx + R, new_posy + R)
        time.sleep(1)

    # THIS IS WHERE THE MATH WILL GO!
    # planet is the planet that is moving,
    # planet.posx is the x coordinate at the end of the time interval,
    # planet.posy is the y coordinate at the end of the time interval.
    # The method should also update the planet's velocity
    def do_the_math(self, planet):
        planet.pos = vector.add(planet.pos, planet.vel)
        #planet.posx = planet.posx + planet.velx
        #planet.posy = planet.posy - planet.vely
        # k1 = self.f(self.pos)
        # print("k1 = ", k1)
        return(planet.pos[0], planet.pos[1])

    # def next_pos(self):
    #     return (vector.add(vector.add(self.pos, self.vel*TIME), self.acceleration*pow(TIME,2)))

    # def acceleration():
    #     f(self.pos)

    # def f(self, r):
    #     total = [0,0]
    #     for planet in self.planet_list:
    #         total = vector.add(total, (vector.scalarMult(planet.mass/pow(vector.mag(vector.sub(r - planet.pos)),3), vector.sub(r, planet.pos))
    #     return(vector.scalarMult(G, total))

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
