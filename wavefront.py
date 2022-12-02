class WavefrontPixel:
    def __init__(self, x, y, parent_value):
        self.x = x
        self.y = y
        self.parent_value = parent_value
        self.value = 0
        self.visited = False
    
    def to_string(self):
        return "visited: " + str(self.visited) + " x: " + str(self.x) + " y: " + str(self.y) + " value: " + str(self.value) + " parent_value: " + str(self.parent_value)
    
    def simple_to_string(self):
        return "(" + str(self.x) + " " + str(self.y) + "), "

def get_neighbours(x, y, map):
    neighbours = []
    if map.get_at((x,y-1)) != 1:
        neighbours.append((x, y-1))
    if map.get_at((x+1, y)) != 1:
        neighbours.append((x+1, y))
    if map.get_at((x,y+1)) != 1:
        neighbours.append((x, y+1))
    if map.get_at((x-1,y)) != 1:
        neighbours.append((x-1, y))
    return neighbours

def wave_front(grid, start, mask):

    # Create a 2D array of pixels
    pixels = [[WavefrontPixel(x, y, 0) for y in range(grid[1])] for x in range(grid[0])]
    # Set the start pixel to 1
    pixels[start[0]][start[1]].visited = 1

    # Create a queue of pixels to process
    queue = []
    queue.append(pixels[start[0]][start[1]])

    # Process the queue
    #iterator = 0
    while len(queue) > 0:
        #if iterator > 4:
        #    break
        # for i in range(len(queue)):
        #     print(queue[i].simple_to_string())
        # Get the next pixel to process
        pixel = queue.pop(0)

        pixel.value = pixel.parent_value + 1

        # Get the value of the pixel
        value = pixel.value

        # Get the neighbors of the pixel
        
        neighbors = get_neighbours(pixel.x, pixel.y, mask)
        #print("6")
        # Process the neighbors
        #print("PARENT: ", pixel.x, pixel.y)
        for neighbor in neighbors:

            if(not pixels[neighbor[0]][neighbor[1]].visited):
                #print("NEIGHBOR: ", neighbor[0], neighbor[1])
                pixels[neighbor[0]][neighbor[1]].parent_value = value
                pixels[neighbor[0]][neighbor[1]].visited = True
                queue.append(pixels[neighbor[0]][neighbor[1]])
        #iterator += 1

    return pixels
